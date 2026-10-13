"""The read-only investigation tools.

Every tool returns an *envelope*:
    {"tool", "source", "generated_at", "data", "security": {...}, "truncated"}
`data` has already been sanitized (redacted + injection-scanned) and trimmed to a
size budget. Tools return structure, not raw dumps: findings first, details after.
"""
from __future__ import annotations

import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from . import logmine
from .backends import Alerts, BackendUnavailable, Logs, Metrics, Traces
from .journal import ChangeJournal, last_manager
from .kube import KubeSource
from .policy import Policy, PolicyError
from .sanitize import Findings, sanitize
from .timeseries import iso, summarize_series

MAX_RESULT_CHARS = 14_000


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def age(value: str | None) -> str | None:
    t = parse_ts(value)
    if not t:
        return None
    s = int((utcnow() - t).total_seconds())
    return f"{s}s" if s < 120 else f"{s // 60}m" if s < 7200 else f"{s // 3600}h"


def owner_workload(pod: dict) -> str | None:
    for ref in pod.get("metadata", {}).get("ownerReferences") or []:
        if ref.get("kind") == "ReplicaSet":
            return re.sub(r"-[a-z0-9]{6,10}$", "", ref["name"])
        if ref.get("kind") in ("StatefulSet", "DaemonSet", "Job"):
            return ref["name"]
    return None


def selector_matches(selector: dict | None, labels: dict | None) -> bool:
    if not selector:
        return False
    labels = labels or {}
    return all(labels.get(k) == v for k, v in selector.items())


def fit(data: Any, budget: int = MAX_RESULT_CHARS) -> tuple[Any, int | bool]:
    """Shrink lists until the JSON fits the budget. Every list keeps its most relevant head
    (tools order their lists most-relevant-first) and keeps its element type: no marker
    strings are inserted, so consumers can rely on the schema. Returns (data, list cap or False)."""
    if len(json.dumps(data, default=str)) <= budget:
        return data, False
    for cap in (40, 25, 15, 10, 6, 3):
        trimmed = _cap_lists(data, cap)
        if len(json.dumps(trimmed, default=str)) <= budget:
            return trimmed, cap
    trimmed = _cap_strings(_cap_lists(data, 3), 300)
    return trimmed, 3


def _cap_lists(obj, cap):
    if isinstance(obj, list):
        return [_cap_lists(x, cap) for x in obj[:cap]]
    if isinstance(obj, dict):
        return {k: _cap_lists(v, cap) for k, v in obj.items()}
    return obj


def _cap_strings(obj, n):
    if isinstance(obj, str):
        return obj if len(obj) <= n else obj[:n] + "…"
    if isinstance(obj, list):
        return [_cap_strings(x, n) for x in obj]
    if isinstance(obj, dict):
        return {k: _cap_strings(v, n) for k, v in obj.items()}
    return obj


@dataclass
class Toolbox:
    kube: KubeSource
    journal: ChangeJournal
    metrics: Metrics
    logs: Logs
    traces: Traces
    alerts: Alerts
    policy: Policy

    # ================================================================ envelope
    def _envelope(self, tool: str, source: str, data: Any) -> dict:
        f = Findings()
        clean = sanitize(data, f)
        clean, cap = fit(clean)
        env = {"tool": tool, "source": source, "generated_at": to_iso(utcnow()), "data": clean,
               "security": f.as_dict(), "truncated": bool(cap)}
        if cap:
            env["note"] = f"result was large: every list was cut to its first {cap} (most relevant) items"
        return env

    # ================================================================ alerts
    def active_alerts(self) -> dict:
        out = []
        for a in self.alerts.active():
            labels = a.get("labels", {})
            ns = labels.get("namespace")
            if ns and ns not in self.policy.allowed_namespaces:
                continue
            out.append({"alert": labels.get("alertname"), "severity": labels.get("severity"),
                        "state": a.get("status", {}).get("state"), "starts_at": a.get("startsAt"),
                        "labels": {k: v for k, v in labels.items() if k not in ("prometheus",)},
                        "summary": a.get("annotations", {}).get("summary"),
                        "description": a.get("annotations", {}).get("description")})
        out.sort(key=lambda x: x.get("starts_at") or "")
        return self._envelope("active_alerts", "alertmanager", {"alerts": out})

    # ================================================================ kubernetes
    def cluster_overview(self, namespace: str) -> dict:
        ns = self.policy.namespace(namespace)
        pods = self.kube.list("pod", ns)
        deployments = self.kube.list("deployment", ns)
        statefulsets = self.kube.list("statefulset", ns)
        services = self.kube.list("service", ns)
        hpas = self.kube.list("hpa", ns)
        pvcs = self.kube.list("pvc", ns)
        slices = self.kube.list("endpointslice", ns)
        findings: list[str] = []

        workloads = []
        for kind, items in (("Deployment", deployments), ("StatefulSet", statefulsets)):
            for d in items:
                spec, st = d.get("spec", {}), d.get("status", {})
                desired = spec.get("replicas", 1)
                ready = st.get("readyReplicas", 0) or 0
                images = sorted({c["image"] for c in spec.get("template", {}).get("spec", {}).get("containers", [])})
                w = {"kind": kind, "name": d["metadata"]["name"], "desired": desired, "ready": ready,
                     "updated": st.get("updatedReplicas"), "available": st.get("availableReplicas"),
                     "images": images, "age": age(d["metadata"].get("creationTimestamp")),
                     "revision": (d["metadata"].get("annotations") or {}).get("deployment.kubernetes.io/revision")}
                conds = [c for c in st.get("conditions") or [] if c.get("status") == "False"]
                if conds:
                    w["failing_conditions"] = [f"{c['type']}: {c.get('reason')} {c.get('message', '')}"[:200] for c in conds]
                if ready < desired:
                    findings.append(f"{kind} {w['name']}: only {ready}/{desired} replicas ready")
                if desired == 0:
                    findings.append(f"{kind} {w['name']} is scaled to 0 replicas")
                workloads.append(w)

        pod_rows = []
        for p in pods:
            meta, st = p["metadata"], p.get("status", {})
            cstats = st.get("containerStatuses") or []
            row = {"name": meta["name"], "workload": owner_workload(p), "phase": st.get("phase"),
                   "ready": f"{sum(1 for c in cstats if c.get('ready'))}/{len(cstats)}",
                   "restarts": sum(c.get("restartCount", 0) for c in cstats),
                   "node": p.get("spec", {}).get("nodeName"),
                   "image": ",".join(sorted({c.get("image", "") for c in cstats})) or None,
                   "age": age(meta.get("creationTimestamp"))}
            for c in cstats:
                waiting = (c.get("state") or {}).get("waiting")
                if waiting:
                    row["waiting"] = waiting.get("reason")
                    findings.append(f"pod {meta['name']} container {c['name']} waiting: {waiting.get('reason')}")
                term = (c.get("lastState") or {}).get("terminated")
                if term:
                    row["last_termination"] = {"container": c["name"], "reason": term.get("reason"),
                                               "exit_code": term.get("exitCode"), "finished_at": term.get("finishedAt")}
                    if term.get("reason") == "OOMKilled":
                        findings.append(f"pod {meta['name']} container {c['name']} was OOMKilled "
                                        f"(exit {term.get('exitCode')}) at {term.get('finishedAt')}")
            if row["restarts"]:
                findings.append(f"pod {meta['name']} has restarted {row['restarts']} times")
            for cond in st.get("conditions") or []:
                if cond.get("type") == "Ready" and cond.get("status") != "True" and st.get("phase") == "Running":
                    row["not_ready_reason"] = cond.get("reason")
                    findings.append(f"pod {meta['name']} is Running but NOT Ready ({cond.get('reason')})")
            if st.get("phase") in ("Pending", "Failed", "Unknown"):
                findings.append(f"pod {meta['name']} phase {st.get('phase')}: {st.get('reason') or ''}".strip())
            pod_rows.append(row)
        pod_rows.sort(key=lambda r: (r["phase"] == "Running" and r["ready"].split("/")[0] == r["ready"].split("/")[1]
                                     and not r["restarts"], r["name"]))

        svc_rows = []
        for s in services:
            name, sel = s["metadata"]["name"], s.get("spec", {}).get("selector")
            ready = not_ready = 0
            for sl in slices:
                if (sl["metadata"].get("labels") or {}).get("kubernetes.io/service-name") == name:
                    for ep in sl.get("endpoints") or []:
                        if (ep.get("conditions") or {}).get("ready"):
                            ready += 1
                        else:
                            not_ready += 1
            matched = [p for p in pods if selector_matches(sel, p["metadata"].get("labels"))]
            backends = defaultdict(set)
            for p in matched:
                for c in p.get("spec", {}).get("containers", []):
                    backends[owner_workload(p) or "?"].add(c.get("image"))
            row = {"name": name, "type": s.get("spec", {}).get("type"), "selector": sel,
                   "ready_endpoints": ready, "not_ready_endpoints": not_ready, "pods_matching_selector": len(matched),
                   "backing_workloads": {w: sorted(i) for w, i in backends.items()}}
            if sel and not matched:
                findings.append(f"service {name} selector {sel} matches NO pods")
            elif sel and ready == 0:
                findings.append(f"service {name} has 0 ready endpoints ({not_ready} not ready)")
            if len(backends) > 1:
                imgs = {img for i in backends.values() for img in i}
                findings.append(f"service {name} routes to {len(backends)} different workloads "
                                f"({', '.join(sorted(backends))}) running images {sorted(imgs)}")
            svc_rows.append(row)

        hpa_rows = []
        for h in hpas:
            spec, st = h.get("spec", {}), h.get("status", {})
            row = {"name": h["metadata"]["name"], "target": spec.get("scaleTargetRef", {}).get("name"),
                   "min": spec.get("minReplicas"), "max": spec.get("maxReplicas"),
                   "current": st.get("currentReplicas"), "desired": st.get("desiredReplicas"),
                   "current_metrics": [
                       {"resource": (m.get("resource") or {}).get("name"),
                        "utilization_pct": ((m.get("resource") or {}).get("current") or {}).get("averageUtilization")}
                       for m in st.get("currentMetrics") or []]}
            if st.get("currentReplicas") and st.get("currentReplicas") >= (spec.get("maxReplicas") or 10 ** 9):
                findings.append(f"HPA {row['name']} is at maxReplicas ({spec.get('maxReplicas')})")
            hpa_rows.append(row)

        pvc_rows = [{"name": c["metadata"]["name"], "phase": c.get("status", {}).get("phase"),
                     "capacity": (c.get("status", {}).get("capacity") or {}).get("storage"),
                     "storage_class": c.get("spec", {}).get("storageClassName")} for c in pvcs]
        for c in pvc_rows:
            if c["phase"] != "Bound":
                findings.append(f"PVC {c['name']} is {c['phase']}")

        data = {"namespace": ns, "findings": findings or ["no obvious resource-level problems"],
                "workloads": workloads, "pods": pod_rows, "services": svc_rows, "hpas": hpa_rows, "pvcs": pvc_rows}
        return self._envelope("cluster_overview", "kubernetes", data)

    def get_events(self, namespace: str, involved_name: str | None = None, minutes: int = 60,
                   warnings_only: bool = False) -> dict:
        ns = self.policy.namespace(namespace)
        minutes = self.policy.minutes(minutes)
        if involved_name:
            self.policy.name(involved_name, "involved_name")
        cutoff = utcnow() - timedelta(minutes=minutes)
        groups: dict[tuple, dict] = {}
        for e in self.kube.list("event", ns):
            last = parse_ts(e.get("lastTimestamp") or e.get("eventTime") or e.get("firstTimestamp")
                            or e.get("metadata", {}).get("creationTimestamp"))
            if not last or last < cutoff:
                continue
            obj = e.get("involvedObject") or e.get("regarding") or {}
            if involved_name and not (obj.get("name") or "").startswith(involved_name):
                continue
            if warnings_only and e.get("type") != "Warning":
                continue
            msg = e.get("message") or e.get("note") or ""
            key = (e.get("reason"), obj.get("kind"), owner_prefix(obj.get("name", "")), logmine.mask(msg)[:160])
            g = groups.get(key)
            first = parse_ts(e.get("firstTimestamp") or e.get("eventTime")) or last
            if not g:
                g = groups[key] = {"type": e.get("type"), "reason": e.get("reason"), "kind": obj.get("kind"),
                                   "objects": set(), "message": msg[:400], "count": 0,
                                   "first_seen": first, "last_seen": last}
            g["objects"].add(obj.get("name"))
            g["count"] += e.get("count") or 1
            g["first_seen"] = min(g["first_seen"], first)
            g["last_seen"] = max(g["last_seen"], last)
        rows = sorted(groups.values(), key=lambda g: g["last_seen"], reverse=True)
        for g in rows:
            g["objects"] = sorted(o for o in g["objects"] if o)[:6]
            g["first_seen"], g["last_seen"] = to_iso(g["first_seen"]), to_iso(g["last_seen"])
        return self._envelope("get_events", "kubernetes", {"namespace": ns, "window_minutes": minutes,
                                                           "event_groups": rows[:60]})

    def recent_changes(self, namespace: str, minutes: int = 120) -> dict:
        ns = self.policy.namespace(namespace)
        minutes = self.policy.minutes(minutes)
        since = to_iso(utcnow() - timedelta(minutes=minutes))
        changes = list(self.journal.records(ns, since))
        journaled = {(c["kind"], c["name"]) for c in changes}

        # Rollouts reconstructed from ReplicaSet history (works for changes made before the broker started).
        rs_by_deploy = defaultdict(list)
        for rs in self.kube.list("replicaset", ns):
            dep = next((r["name"] for r in rs["metadata"].get("ownerReferences") or [] if r["kind"] == "Deployment"), None)
            if dep:
                rs_by_deploy[dep].append(rs)
        for dep, rss in rs_by_deploy.items():
            rss.sort(key=lambda r: int((r["metadata"].get("annotations") or {}).get("deployment.kubernetes.io/revision", 0)))
            for prev, cur in zip([None] + rss[:-1], rss):
                created = cur["metadata"].get("creationTimestamp", "")
                if created < since:
                    continue
                img = lambda r: sorted(c["image"] for c in r["spec"]["template"]["spec"]["containers"])
                env_changes = _template_diff(prev, cur) if prev else []
                changes.append({
                    "time": created, "kind": "rollout", "namespace": ns, "name": dep, "change": "new-revision",
                    "revision": (cur["metadata"].get("annotations") or {}).get("deployment.kubernetes.io/revision"),
                    "replicaset": cur["metadata"]["name"],
                    "fields": ([{"field": "image", "old": img(prev), "new": img(cur)}] if prev and img(prev) != img(cur) else [])
                              + env_changes,
                    "replicas_now": cur.get("status", {}).get("replicas"),
                    "source": "replicaset-history"})

        # Last write to config-like objects, when the journal has no record of it.
        for kind in ("configmap", "service", "deployment", "statefulset", "hpa"):
            for obj in self.kube.list(kind, ns):
                mgr = last_manager(obj)
                if mgr.get("time", "") >= since and (kind, obj["metadata"]["name"]) not in journaled:
                    if kind == "deployment" and mgr.get("manager") == "kube-controller-manager":
                        continue  # status churn
                    changes.append({"time": mgr["time"], "kind": kind, "namespace": ns,
                                    "name": obj["metadata"]["name"], "change": "last-write",
                                    "actor": mgr, "fields": [],
                                    "note": "content diff unavailable (change predates the broker's journal)",
                                    "source": "managedFields"})
        changes.sort(key=lambda c: c["time"], reverse=True)  # newest first: trimming keeps the latest
        return self._envelope("recent_changes", "kubernetes", {
            "namespace": ns, "window_minutes": minutes, "journal_since": self.journal.started_at,
            "changes": changes[:60]})

    def describe(self, kind: str, namespace: str, name: str) -> dict:
        k = self.policy.kind(kind)
        ns = None if k == "node" else self.policy.namespace(namespace)
        self.policy.name(name)
        obj = self.kube.get(k, ns, name)
        if obj is None:
            candidates = [o["metadata"]["name"] for o in self.kube.list(k, ns) if o["metadata"]["name"].startswith(name[:6])]
            raise PolicyError(f"{k} {name!r} not found in {ns}; similar: {candidates[:10]}")
        return self._envelope("describe", "kubernetes", {"kind": k, **trim_object(k, obj)})

    def pod_logs(self, namespace: str, pod: str, container: str | None = None, previous: bool = False,
                 tail: int = 300, minutes: int | None = None) -> dict:
        ns = self.policy.namespace(namespace)
        self.policy.name(pod, "pod")
        if container:
            self.policy.name(container, "container")
        tail = max(10, min(int(tail), self.policy.max_log_lines))
        if self.kube.get("pod", ns, pod) is None:
            similar = [p["metadata"]["name"] for p in self.kube.list("pod", ns) if p["metadata"]["name"].startswith(pod)]
            raise PolicyError(f"pod {pod!r} not found; pods with that prefix: {similar[:10]}")
        text = self.kube.logs(ns, pod, container, previous, tail, (minutes or 0) * 60 or None)
        lines = text.splitlines()
        data = {"pod": pod, "container": container, "previous_instance": previous,
                **logmine.mine(lines, source=pod), "last_lines": [l[:400] for l in lines[-15:]]}
        return self._envelope("pod_logs", "kubernetes-logs", data)

    # ================================================================ logs (Loki)
    def search_logs(self, namespace: str, app: str | None = None, pod: str | None = None,
                    contains: str | None = None, level: str | None = None, minutes: int = 30,
                    limit: int = 1000) -> dict:
        ns = self.policy.namespace(namespace)
        minutes = self.policy.minutes(minutes)
        sel = [f'namespace={json.dumps(ns)}']
        if app:
            sel.append(f'app={json.dumps(self.policy.name(app, "app"))}')
        if pod:
            sel.append(f'pod={json.dumps(self.policy.name(pod, "pod"))}')
        if level:
            if level not in ("error", "warning", "info", "debug"):
                raise PolicyError("level must be one of error|warning|info|debug")
            sel.append(f'level={json.dumps(level)}')
        logql = "{" + ", ".join(sel) + "}"
        if contains:
            if len(contains) > 200:
                raise PolicyError("contains filter too long")
            logql += f" |= {json.dumps(contains)}"
        end = time.time()
        rows = self.logs.query_range(logql, end - minutes * 60, end, max(10, min(int(limit), 5000)))
        mined = logmine.mine([(iso(int(ts) / 1e9), line) for ts, line, _ in rows])
        by_pod = Counter(lbl.get("pod") for _, _, lbl in rows)
        return self._envelope("search_logs", "loki", {
            "logql": logql, "window_minutes": minutes, **mined,
            "lines_by_pod": dict(by_pod.most_common(15))})

    # ================================================================ metrics
    def workload_metrics(self, namespace: str, workload: str, minutes: int = 30) -> dict:
        ns = self.policy.namespace(namespace)
        w = self.policy.name(workload, "workload")
        minutes = self.policy.minutes(minutes)
        pod_re = f"{w}-[a-z0-9]+(-[a-z0-9]+)?"
        sel = f'namespace="{ns}", svc="{w}"'
        csel = f'namespace="{ns}", pod=~"{pod_re}", container!="", container!="POD"'
        queries = {
            "request_rate_rps": (f"sum(rate(http_requests_total{{{sel}}}[1m]))", "req/s"),
            "error_ratio_5xx": (f'sum(rate(http_requests_total{{{sel}, code=~"5.."}}[1m])) / '
                                f"clamp_min(sum(rate(http_requests_total{{{sel}}}[1m])), 0.001)", "ratio"),
            "errors_by_pod_rps": (f'sum by (pod) (rate(http_requests_total{{{sel}, code=~"5.."}}[1m]))', "req/s"),
            "latency_p95_seconds": (f"histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{{{sel}}}[1m])))", "s"),
            "dependency_failures_rps": (f'sum by (dep, outcome) (rate(dependency_requests_total{{{sel}, outcome!="ok"}}[1m]))', "req/s"),
            "cpu_cores": (f"sum by (pod) (rate(container_cpu_usage_seconds_total{{{csel}}}[1m]))", "cores"),
            "cpu_throttled_ratio": (f"sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{{{csel}}}[1m])) / "
                                    f"clamp_min(sum by (pod) (rate(container_cpu_cfs_periods_total{{{csel}}}[1m])), 0.001)", "ratio"),
            "memory_working_set_bytes": (f"sum by (pod) (container_memory_working_set_bytes{{{csel}}})", "bytes"),
            "memory_limit_bytes": (f'max(kube_pod_container_resource_limits{{namespace="{ns}", pod=~"{pod_re}", resource="memory"}})', "bytes"),
            "container_restarts": (f'sum by (pod) (kube_pod_container_status_restarts_total{{namespace="{ns}", pod=~"{pod_re}"}})', "count"),
            "db_errors_rps": (f"sum by (kind) (rate(db_errors_total{{{sel}}}[1m]))", "req/s"),
        }
        end = time.time()
        start = end - minutes * 60
        step = max(15, minutes * 60 // 120)
        signals, errors = {}, {}
        for name, (q, unit) in queries.items():
            try:
                series = self.metrics.query_range(q, start, end, step)
            except BackendUnavailable as exc:
                errors[name] = str(exc)[:200]
                continue
            if series:
                signals[name] = [summarize_series(s["metric"], s["values"], unit) for s in series[:8]]
        if not signals and errors:
            raise BackendUnavailable(next(iter(errors.values())))
        return self._envelope("workload_metrics", "prometheus", {
            "namespace": ns, "workload": w, "window_minutes": minutes, "step_seconds": step,
            "signals": signals, "no_data": sorted(set(queries) - set(signals) - set(errors)), "errors": errors})

    def query_metrics(self, promql: str, minutes: int = 30, step_seconds: int = 30) -> dict:
        q = self.policy.promql(promql)
        minutes = self.policy.minutes(minutes)
        step = max(5, min(int(step_seconds), 600))
        if minutes * 60 / step > 1000:
            step = int(minutes * 60 / 1000) + 1
        end = time.time()
        series = self.metrics.query_range(q, end - minutes * 60, end, step)
        summaries = [summarize_series(s["metric"], s["values"]) for s in series]
        summaries.sort(key=lambda s: -(s.get("max") or 0))
        return self._envelope("query_metrics", "prometheus", {
            "promql": q, "window_minutes": minutes, "step_seconds": step, "series_count": len(series),
            "series": summaries[:12]})

    # ================================================================ traces
    def find_traces(self, service: str, minutes: int = 15, errors_only: bool = True, limit: int = 20) -> dict:
        svc = self.policy.name(service, "service")
        minutes = self.policy.minutes(minutes)
        end = time.time()
        traces = self.traces.find_traces(svc, end - minutes * 60, end, max(1, min(int(limit), 50)), errors_only)
        return self._envelope("find_traces", "jaeger", {"service": svc, "window_minutes": minutes,
                                                        "errors_only": errors_only, **analyze_traces(traces)})

    def service_map(self, minutes: int = 30) -> dict:
        minutes = self.policy.minutes(minutes)
        deps = self.traces.dependencies(time.time(), minutes * 60)
        edges = sorted(({"caller": d.get("parent"), "callee": d.get("child"), "calls": d.get("callCount")}
                        for d in deps), key=lambda e: -(e["calls"] or 0))
        return self._envelope("service_map", "jaeger", {"window_minutes": minutes, "edges": edges})


# ==================================================================== helpers
def owner_prefix(name: str) -> str:
    return re.sub(r"-[a-z0-9]{5}$", "", re.sub(r"-[a-z0-9]{8,10}-[a-z0-9]{5}$", "", name))


def _template_diff(prev: dict, cur: dict) -> list[dict]:
    from .journal import interesting_fields, diff
    keep = lambda d: {k: v for k, v in d.items() if k not in ("spec.replicas", "template.labels")}
    wrap = lambda rs: {"spec": {"template": rs["spec"]["template"]}}
    return [c for c in diff(keep(interesting_fields("deployment", wrap(prev))), keep(interesting_fields("deployment", wrap(cur))))
            if not c["field"].endswith(".image")][:20]


def trim_object(kind: str, obj: dict) -> dict:
    meta = obj.get("metadata", {})
    ann = {k: v for k, v in (meta.get("annotations") or {}).items()
           if "last-applied-configuration" not in k}
    out = {"metadata": {"name": meta.get("name"), "namespace": meta.get("namespace"), "labels": meta.get("labels"),
                        "annotations": ann or None, "created": meta.get("creationTimestamp"),
                        "generation": meta.get("generation"),
                        "owners": [f"{o['kind']}/{o['name']}" for o in meta.get("ownerReferences") or []],
                        "write_history": sorted(({"manager": m.get("manager"), "operation": m.get("operation"),
                                                  "time": m.get("time"), "subresource": m.get("subresource")}
                                                 for m in meta.get("managedFields") or []),
                                                key=lambda m: m.get("time") or "")[-8:]}}
    spec = obj.get("spec") or {}
    if kind in ("deployment", "statefulset", "replicaset", "daemonset"):
        tpl = spec.get("template", {})
        out["spec"] = {"replicas": spec.get("replicas"), "selector": spec.get("selector"),
                       "strategy": spec.get("strategy") or spec.get("updateStrategy"),
                       "template_labels": tpl.get("metadata", {}).get("labels"),
                       "containers": [trim_container(c) for c in tpl.get("spec", {}).get("containers", [])],
                       "volumes": tpl.get("spec", {}).get("volumes")}
        out["status"] = {k: v for k, v in (obj.get("status") or {}).items() if k != "conditions"}
        out["conditions"] = (obj.get("status") or {}).get("conditions")
    elif kind == "pod":
        out["spec"] = {"node": spec.get("nodeName"), "containers": [trim_container(c) for c in spec.get("containers", [])],
                       "volumes": spec.get("volumes")}
        st = obj.get("status") or {}
        out["status"] = {"phase": st.get("phase"), "conditions": st.get("conditions"), "podIP": st.get("podIP"),
                         "containerStatuses": st.get("containerStatuses"), "qosClass": st.get("qosClass")}
    elif kind == "configmap":
        out["data"] = obj.get("data")
    elif kind == "service":
        out["spec"] = {k: spec.get(k) for k in ("type", "selector", "ports", "clusterIP")}
    elif kind == "node":
        st = obj.get("status") or {}
        out["status"] = {"conditions": [{k: c.get(k) for k in ("type", "status", "reason", "lastTransitionTime")}
                                        for c in st.get("conditions") or []],
                         "allocatable": st.get("allocatable"), "capacity": st.get("capacity")}
        out["spec"] = {"taints": spec.get("taints"), "unschedulable": spec.get("unschedulable")}
    else:
        out["spec"] = spec
        out["status"] = obj.get("status")
    return out


def trim_container(c: dict) -> dict:
    env = []
    for e in c.get("env") or []:
        if "value" in e:
            env.append({"name": e["name"], "value": e["value"]})
        else:
            vf = e.get("valueFrom") or {}
            src = next(iter(vf), "valueFrom")
            ref = vf.get(src) or {}
            env.append({"name": e["name"], "value": f"<from {src} {ref.get('name', '')} {ref.get('key', ref.get('fieldPath', ''))}>".strip()})
    return {k: v for k, v in {
        "name": c.get("name"), "image": c.get("image"), "args": c.get("args"), "env": env or None,
        "envFrom": c.get("envFrom"), "resources": c.get("resources"), "livenessProbe": c.get("livenessProbe"),
        "readinessProbe": c.get("readinessProbe"), "ports": c.get("ports")}.items() if v}


def analyze_traces(traces: list[dict]) -> dict:
    """Find where errors originate (deepest failing span) and where time goes."""
    origins: Counter = Counter()
    examples: dict = {}
    slowest = []
    self_time: dict[str, list[float]] = defaultdict(list)
    error_traces = 0
    for t in traces:
        procs = {pid: p.get("serviceName") for pid, p in (t.get("processes") or {}).items()}
        spans = t.get("spans") or []
        by_id = {s["spanID"]: s for s in spans}
        children = defaultdict(list)
        for s in spans:
            for ref in s.get("references") or []:
                if ref.get("refType") == "CHILD_OF" and ref.get("spanID") in by_id:
                    children[ref["spanID"]].append(s["spanID"])
        tags = {s["spanID"]: {tg["key"]: tg.get("value") for tg in s.get("tags") or []} for s in spans}

        def is_err(sid):
            tg = tags[sid]
            code = tg.get("http.status_code") or tg.get("http.response.status_code")
            return tg.get("error") in (True, "true") or tg.get("otel.status_code") == "ERROR" or (
                isinstance(code, (int, float)) and code >= 500) or (isinstance(code, str) and code.isdigit() and int(code) >= 500)

        def has_err_desc(sid):
            return any(is_err(c) or has_err_desc(c) for c in children[sid])

        errs = [sid for sid in by_id if is_err(sid)]
        if errs:
            error_traces += 1
        for sid in errs:
            if not has_err_desc(sid):
                s = by_id[sid]
                svc = procs.get(s.get("processID"), "?")
                msg = (tags[sid].get("otel.status_description") or tags[sid].get("exception.message")
                       or tags[sid].get("error.type") or "")
                code = tags[sid].get("http.status_code") or tags[sid].get("http.response.status_code")
                key = (svc, s.get("operationName"), str(code or ""), str(msg)[:120])
                origins[key] += 1
                examples.setdefault(key, t.get("traceID"))
        roots = [s for s in spans if not s.get("references")]
        if roots:
            r = roots[0]
            slowest.append({"trace_id": t.get("traceID"), "duration_ms": round(r.get("duration", 0) / 1000, 1),
                            "root": f"{procs.get(r.get('processID'))} {r.get('operationName')}",
                            "error": bool(errs)})
        for s in spans:
            child_total = sum(by_id[c].get("duration", 0) for c in children[s["spanID"]])
            self_time[procs.get(s.get("processID"), "?")].append(max(0, s.get("duration", 0) - child_total) / 1000)
    slowest.sort(key=lambda x: -x["duration_ms"])
    return {
        "traces_examined": len(traces), "traces_with_errors": error_traces,
        "error_origins": [{"service": k[0], "operation": k[1], "status_code": k[2] or None, "message": k[3] or None,
                           "count": n, "example_trace_id": examples[k]} for k, n in origins.most_common(10)],
        "slowest_traces": slowest[:8],
        "mean_self_time_ms_by_service": {k: round(sum(v) / len(v), 1) for k, v in
                                         sorted(self_time.items(), key=lambda kv: -sum(kv[1]))},
    }
