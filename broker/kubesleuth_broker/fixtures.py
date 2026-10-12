"""Offline mode: serve a recorded incident snapshot instead of a live cluster.

Used for unit tests, CI, and `make demo-offline` (no cluster, no Docker).
Timestamps in fixtures are written relative to "now" so a snapshot stays valid:
  "@-300"      -> ISO time 300s ago        "@epoch-300" -> unix seconds
  "@ns-300"    -> unix nanoseconds (Loki)  "@us-300"    -> unix microseconds (Jaeger)
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from .backends import BackendUnavailable
from .journal import ChangeJournal
from .kube import FixtureKube

_REL = re.compile(r"^@(epoch|ns|us)?(-?\d+)$")
_EMBEDDED = re.compile(r'"@(-?\d+)"')


def resolve_times(obj, now: float):
    if isinstance(obj, str):
        m = _REL.match(obj)
        if not m:
            if '"@' in obj:  # relative times embedded in JSON log lines
                return _EMBEDDED.sub(lambda e: '"' + resolve_times("@" + e.group(1), now) + '"', obj)
            return obj
        t = now + int(m.group(2))
        unit = m.group(1)
        if unit == "epoch":
            return t
        if unit == "ns":
            return str(int(t * 1e9))
        if unit == "us":
            return int(t * 1e6)
        return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(obj, list):
        return [resolve_times(x, now) for x in obj]
    if isinstance(obj, dict):
        return {k: resolve_times(v, now) for k, v in obj.items()}
    return obj


class _Matcher:
    def __init__(self, rules: list[dict], key: str):
        self.rules, self.key = rules, key

    def find(self, query: str):
        for rule in self.rules:
            if all(s in query for s in rule.get("match", [])):
                return rule[self.key]
        return []


class FixtureMetrics:
    def __init__(self, rules):
        self._m = _Matcher(rules, "series")

    def query_range(self, promql, start, end, step):
        return self._m.find(promql)


class FixtureLogs:
    def __init__(self, rules):
        self._m = _Matcher(rules, "lines")

    def query_range(self, logql, start, end, limit):
        return [(l["ts"], l["line"], l.get("labels", {})) for l in self._m.find(logql)][-limit:]


class FixtureTraces:
    def __init__(self, traces: dict, deps: list):
        self._t, self._d = traces, deps

    def find_traces(self, service, start, end, limit, errors_only):
        return self._t.get(service, [])[:limit]

    def dependencies(self, end, lookback_s):
        return self._d


class FixtureAlerts:
    def __init__(self, alerts):
        self._a = alerts

    def active(self):
        return self._a


class Unavailable:
    """Stand-in for a backend that is not deployed (exercises the agent's robustness)."""

    def __init__(self, name):
        self.name = name

    def __getattr__(self, item):
        def fail(*a, **k):
            raise BackendUnavailable(f"{self.name} is not available in this environment")
        return fail


def load(path: str | Path):
    doc = resolve_times(json.loads(Path(path).read_text()), time.time())
    journal = ChangeJournal()
    journal.preload(doc.get("journal", []))
    kube = FixtureKube(doc.get("kube", {}), doc.get("logs", {}))
    metrics = FixtureMetrics(doc["metrics"]) if "metrics" in doc else Unavailable("prometheus")
    logs = FixtureLogs(doc["loki"]) if "loki" in doc else Unavailable("loki")
    traces = FixtureTraces(doc["traces"], doc.get("dependencies", [])) if "traces" in doc else Unavailable("jaeger")
    alerts = FixtureAlerts(doc.get("alerts", []))
    return kube, journal, metrics, logs, traces, alerts
