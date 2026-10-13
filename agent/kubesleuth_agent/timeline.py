"""Deterministic timeline built from structured tool results (never from model prose).

Every entry cites the observation it came from. The model reads this to judge
temporal precedence (did the change happen *before* the onset?).
"""
from __future__ import annotations

from dataclasses import dataclass

from .observations import ObservationStore

def _dicts(xs) -> list:
    """Tool results are untrusted input: tolerate missing or mistyped list items."""
    return [x for x in xs if isinstance(x, dict)] if isinstance(xs, list) else []



@dataclass
class TimelineEntry:
    time: str
    event: str
    kind: str          # change | onset | event | alert | log
    observation_id: str
    source: str


INTERESTING_SIGNALS = {"error_ratio_5xx", "errors_by_pod_rps", "latency_p95_seconds", "dependency_failures_rps",
                       "memory_working_set_bytes", "cpu_throttled_ratio", "container_restarts", "db_errors_rps",
                       "request_rate_rps"}


def _fmt(v, n=60):
    s = str(v)
    return s if len(s) <= n else s[:n] + "…"


def build(store: ObservationStore) -> list[TimelineEntry]:
    out: list[TimelineEntry] = []
    for o in store.all():
        if not o.ok:
            continue
        try:
            d = o.envelope.get("data") or {}
            if o.tool == "recent_changes":
                for c in _dicts(d.get("changes")):
                    fields = "; ".join(f"{f['field']} {_fmt(f.get('old'), 30)} → {_fmt(f.get('new'), 30)}"
                                       + (" (since reverted)" if f.get("in_effect") is False else "")
                                       for f in _dicts(c.get("fields"))[:3])
                    actor = (c.get("actor") or {}).get("manager")
                    out.append(TimelineEntry(c["time"], f"{c['kind']}/{c['name']} {c['change']}"
                                             + (f": {fields}" if fields else "") + (f" (by {actor})" if actor else ""),
                                             "change", o.id, o.source))
            elif o.tool == "workload_metrics":
                for name, series in (d.get("signals") or {}).items():
                    if name not in INTERESTING_SIGNALS:
                        continue
                    onsets = [s for s in _dicts(series) if s.get("onset")]
                    if not onsets:
                        continue
                    first = min(onsets, key=lambda s: s["onset"]["time"])
                    on = first["onset"]
                    if len(onsets) > 1:  # e.g. the same signal on 4 pods: one line, not four
                        what = f"{name} on {len(onsets)}/{len(series)} series"
                    else:
                        lbl = ",".join(str(v) for v in (first.get("labels") or {}).values())
                        what = f"{name}{'[' + lbl + ']' if lbl else ''}"
                    out.append(TimelineEntry(on["time"], f"{d.get('workload')} {what} {on['direction']}: "
                                             f"{on['baseline']} → {on['value_after']}", "onset", o.id, o.source))
            elif o.tool == "query_metrics":
                for s in _dicts(d.get("series")):
                    if s.get("onset"):
                        out.append(TimelineEntry(s["onset"]["time"], f"{_fmt(d.get('promql'), 70)} {s['onset']['direction']}",
                                                 "onset", o.id, o.source))
            elif o.tool == "get_events":
                for g in _dicts(d.get("event_groups")):
                    if g.get("type") == "Warning" or g.get("reason") in ("ScalingReplicaSet", "Killing", "SuccessfulRescale"):
                        out.append(TimelineEntry(g["first_seen"], f"event {g['reason']} x{g['count']} on {g['kind']}/"
                                                 f"{','.join(g['objects'][:2])}: {_fmt(g['message'], 90)}", "event", o.id, o.source))
            elif o.tool == "active_alerts":
                for a in _dicts(d.get("alerts")):
                    out.append(TimelineEntry(a.get("starts_at") or "", f"alert {a['alert']} fired ({a.get('severity')})",
                                             "alert", o.id, o.source))
            elif o.tool in ("search_logs", "pod_logs"):
                for t in _dicts(d.get("templates")):
                    if t["level"] in ("error", "warning") and t.get("first_seen"):
                        out.append(TimelineEntry(t["first_seen"], f"first log: {_fmt(t['pattern'], 90)} (x{t['count']})",
                                                 "log", o.id, o.source))
        except (KeyError, TypeError, AttributeError, ValueError):
            continue  # one malformed result must never break the investigation
    seen, uniq = set(), []
    for e in sorted((e for e in out if e.time), key=lambda e: e.time):
        key = (e.time[:16], e.event[:60])
        if key not in seen:
            seen.add(key)
            uniq.append(e)
    return uniq


def render(entries: list[TimelineEntry], limit: int = 30) -> str:
    if len(entries) > limit:  # keep changes and alerts, then the earliest onsets/events
        keep = [e for e in entries if e.kind in ("change", "alert")]
        rest = [e for e in entries if e.kind not in ("change", "alert")][: max(0, limit - len(keep))]
        entries = sorted(keep + rest, key=lambda e: e.time)
    return "\n".join(f"{e.time}  [{e.kind}] {e.event}  ({e.observation_id})" for e in entries)
