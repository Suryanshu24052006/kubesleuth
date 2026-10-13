"""Change journal: a field-level history of what changed in the cluster.

The Kubernetes API only stores the *current* state of an object. To answer
"what changed right before the incident?" with real diffs (DB_POOL_SIZE 4 -> 30,
livenessProbe.timeoutSeconds 3 -> 1, Service selector app=inventory -> app=inventory-v2)
the broker watches the objects that usually carry change (Deployments, StatefulSets,
ConfigMaps, Services, HPAs) with list+watch, the same pattern as a client-go
informer, and records diffs of the fields that matter.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone

from .sanitize import SENSITIVE_KEY

log = logging.getLogger("kubesleuth.journal")


def _mask(key: str, value):
    """Record *that* a credential-like value changed, never the value itself."""
    if isinstance(value, str) and SENSITIVE_KEY.search(key) and not value.startswith("<valueFrom"):
        import hashlib
        return "[REDACTED sha256:" + hashlib.sha256(value.encode()).hexdigest()[:8] + "]"
    return value


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _container_fields(prefix: str, c: dict) -> dict:
    out = {f"{prefix}.image": c.get("image")}
    for e in c.get("env") or []:
        if "value" in e:
            out[f"{prefix}.env.{e['name']}"] = _mask(e["name"], e["value"])
        elif e.get("valueFrom"):
            out[f"{prefix}.env.{e['name']}"] = "<valueFrom " + json.dumps(e["valueFrom"], sort_keys=True) + ">"
    for ef in c.get("envFrom") or []:
        out[f"{prefix}.envFrom.{json.dumps(ef, sort_keys=True)}"] = "present"
    for key in ("resources", "livenessProbe", "readinessProbe", "startupProbe", "args", "command"):
        if c.get(key) is not None:
            out[f"{prefix}.{key}"] = json.dumps(c[key], sort_keys=True)
    return out


def interesting_fields(kind: str, obj: dict) -> dict:
    spec = obj.get("spec") or {}
    if kind in ("deployment", "statefulset"):
        tpl = (spec.get("template") or {})
        out = {"spec.replicas": spec.get("replicas"),
               "spec.strategy": json.dumps(spec.get("strategy") or spec.get("updateStrategy"), sort_keys=True),
               "template.labels": json.dumps((tpl.get("metadata") or {}).get("labels"), sort_keys=True),
               "template.annotations": json.dumps((tpl.get("metadata") or {}).get("annotations"), sort_keys=True)}
        for c in (tpl.get("spec") or {}).get("containers") or []:
            out.update(_container_fields(f"containers[{c['name']}]", c))
        for v in (tpl.get("spec") or {}).get("volumes") or []:
            out[f"volumes[{v['name']}]"] = json.dumps({k: v[k] for k in v if k != "name"}, sort_keys=True)
        return out
    if kind == "configmap":
        return {f"data.{k}": _mask(k, v) for k, v in (obj.get("data") or {}).items()}
    if kind == "service":
        return {"spec.selector": json.dumps(spec.get("selector"), sort_keys=True),
                "spec.ports": json.dumps(spec.get("ports"), sort_keys=True),
                "spec.type": spec.get("type")}
    if kind == "hpa":
        return {"spec.minReplicas": spec.get("minReplicas"), "spec.maxReplicas": spec.get("maxReplicas"),
                "spec.metrics": json.dumps(spec.get("metrics"), sort_keys=True)}
    return {}


def diff(old: dict, new: dict) -> list[dict]:
    changes = []
    for key in sorted(set(old) | set(new)):
        a, b = old.get(key), new.get(key)
        if a != b:
            changes.append({"field": key, "old": a, "new": b})
    return changes


def last_manager(obj: dict) -> dict:
    """Who last changed the object's spec/data. Status writes are ignored: controllers update
    status constantly, which would otherwise hide the human (kubectl) or tool that made the change."""
    entries = (obj.get("metadata") or {}).get("managedFields") or []
    entries = [e for e in entries if e.get("time") and e.get("subresource") != "status"]
    if not entries:
        return {}
    e = max(entries, key=lambda e: e["time"])
    return {"manager": e.get("manager"), "operation": e.get("operation"), "time": e.get("time"),
            "subresource": e.get("subresource")}


class ChangeJournal:
    def __init__(self, maxlen: int = 2000):
        self._records: deque = deque(maxlen=maxlen)
        self._state: dict[str, dict] = {}
        self._lock = threading.Lock()
        self.started_at = now_iso()

    # ---------------------------------------------------------------- recording
    def observe(self, kind: str, event_type: str, obj: dict, baseline: bool = False) -> None:
        meta = obj.get("metadata") or {}
        key = f"{kind}/{meta.get('namespace')}/{meta.get('name')}"
        fields = interesting_fields(kind, obj)
        with self._lock:
            prev = self._state.get(key)
            if event_type == "DELETED":
                self._state.pop(key, None)
                self._add(kind, meta, "deleted", [], obj)
                return
            self._state[key] = fields
            if baseline:
                return
            if prev is None:
                self._add(kind, meta, "created", [], obj)
                return
            changes = diff(prev, fields)
            if changes:
                self._add(kind, meta, "modified", changes, obj)

    def _add(self, kind, meta, change, fields, obj):
        mgr = last_manager(obj)
        self._records.append({
            "time": now_iso() if change == "deleted" else (mgr.get("time") or now_iso()),
            "observed_at": now_iso(),
            "kind": kind, "namespace": meta.get("namespace"), "name": meta.get("name"),
            "change": change, "fields": fields,
            "actor": {k: v for k, v in mgr.items() if v} if change != "deleted" else {},
            "source": "change-journal",
        })

    def preload(self, records: list[dict]) -> None:
        with self._lock:
            self._records.extend(records)

    # ---------------------------------------------------------------- reading
    def records(self, namespace: str, since_iso: str) -> list[dict]:
        """Matching records, each field annotated with whether that value is STILL in effect.
        A change that was later reverted (by a reset, a rollback or a controller) is usually not
        the cause of an ongoing incident."""
        with self._lock:
            out = []
            for r in self._records:
                if r["namespace"] != namespace or r["time"] < since_iso:
                    continue
                current = self._state.get(f"{r['kind']}/{r['namespace']}/{r['name']}")
                rec = dict(r)
                if current is not None and r.get("fields"):
                    rec["fields"] = [{**f, "in_effect": current.get(f["field"]) == f.get("new")} for f in r["fields"]]
                    rec["still_in_effect"] = any(f["in_effect"] for f in rec["fields"])
                elif r["change"] == "deleted":
                    rec["still_in_effect"] = current is None
                out.append(rec)
            return out

    # ---------------------------------------------------------------- live watch
    def start(self, kube, namespaces: list[str]) -> None:
        for kind, list_fn in kube.watch_targets().items():
            for ns in namespaces:
                t = threading.Thread(target=self._watch_loop, args=(kind, list_fn, ns), daemon=True,
                                     name=f"journal-{kind}-{ns}")
                t.start()

    def _watch_loop(self, kind, list_fn, ns):
        from kubernetes import watch
        from kubernetes.client import ApiClient
        ser = ApiClient().sanitize_for_serialization
        while True:
            try:
                listing = list_fn(ns)
                for item in listing.items:
                    self.observe(kind, "ADDED", ser(item), baseline=True)
                rv = listing.metadata.resource_version
                w = watch.Watch()
                for ev in w.stream(list_fn, ns, resource_version=rv, timeout_seconds=300):
                    self.observe(kind, ev["type"], ser(ev["object"]))
            except Exception as exc:  # 410 Gone, network blips: relist
                log.warning("journal watch %s/%s restarting: %s", kind, ns, exc)
                time.sleep(3)
