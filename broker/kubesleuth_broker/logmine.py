"""Log template mining: turn thousands of lines into a handful of patterns.

A simplified Drain-style approach: parse JSON logs where possible, mask variable
tokens (numbers, ids, IPs, durations, quoted values), and group identical masked
messages. Each group keeps counts, first/last timestamps and one real example.
This is the "summarize logs before they reach the model" step: the model sees
`count=812 "stock lookup failed error=OperationalError detail=FATAL: sorry, too
many clients already"` instead of 812 raw lines.
"""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field

_MASKS = [
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "<uuid>"),
    (re.compile(r"\b\d{1,3}(\.\d{1,3}){3}(:\d+)?\b"), "<ip>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ][\d:.]+Z?\b"), "<ts>"),
    (re.compile(r"\b0x[0-9a-f]+\b", re.I), "<hex>"),
    (re.compile(r"\b[0-9a-f]{16,}\b", re.I), "<hex>"),
    (re.compile(r"\b[a-z0-9]+(-[a-z0-9]+)*-[a-z0-9]{8,10}-[a-z0-9]{5}\b"), "<pod>"),
    (re.compile(r"\b\d+(\.\d+)?(ms|s|m|h|Mi|Gi|Ki|MB|KB|GB|%)?\b"), "<n>"),
]
_LEVEL = re.compile(r"\b(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL|PANIC)\b")
_SKIP_FIELDS = {"ts", "time", "timestamp", "@timestamp", "level", "lvl", "severity", "svc", "version", "msg", "message"}
_VOLATILE_FIELDS = {"user", "sku", "trace_id", "span_id", "request_id", "pod", "events", "buffered_events",
                    "buffered_mb", "ok", "err", "digest"}


@dataclass
class Template:
    pattern: str
    level: str
    count: int = 0
    first_ts: str | None = None
    last_ts: str | None = None
    example: str = ""
    sources: set = field(default_factory=set)


def mask(text: str) -> str:
    for rx, repl in _MASKS:
        text = rx.sub(repl, text)
    return re.sub(r"\s+", " ", text).strip()


def parse_line(line: str) -> tuple[str, str, str | None]:
    """Return (level, message-for-templating, timestamp)."""
    line = line.rstrip()
    ts = None
    # kubectl --timestamps / Loki style prefix
    m = re.match(r"^(\d{4}-\d{2}-\d{2}T[\d:.]+Z?)\s+(.*)$", line)
    if m:
        ts, line = m.group(1), m.group(2)
    if line.startswith("{"):
        try:
            doc = json.loads(line)
            level = str(doc.get("level") or doc.get("severity") or doc.get("lvl") or "info").lower()
            msg = str(doc.get("msg") or doc.get("message") or "")
            extras = [f"{k}={v}" for k, v in doc.items()
                      if k not in _SKIP_FIELDS and k not in _VOLATILE_FIELDS and v not in (None, "")]
            ts = ts or doc.get("ts") or doc.get("time") or doc.get("timestamp")
            return _norm_level(level), (msg + (" " + " ".join(extras) if extras else "")).strip(), ts
        except (ValueError, AttributeError):
            pass
    lm = _LEVEL.search(line[:120])
    level = _norm_level(lm.group(1).lower()) if lm else "info"
    if level == "info" and re.search(r"(?i)traceback|exception|error|fatal|panic|refused|timeout", line):
        level = "error"
    return level, line, ts


def _norm_level(level: str) -> str:
    return {"warn": "warning", "critical": "error", "fatal": "error", "panic": "error"}.get(level, level)


def mine(lines, source: str = "", max_templates: int = 25) -> dict:
    """`lines` is an iterable of str or (timestamp, str)."""
    groups: "OrderedDict[str, Template]" = OrderedDict()
    total = 0
    by_level: dict[str, int] = {}
    for item in lines:
        ts_hint, raw = (item if isinstance(item, tuple) else (None, item))
        if not raw or not raw.strip():
            continue
        total += 1
        level, msg, ts = parse_line(raw)
        ts = ts or ts_hint
        by_level[level] = by_level.get(level, 0) + 1
        key = f"{level}|{mask(msg)[:300]}"
        t = groups.get(key)
        if t is None:
            t = groups[key] = Template(pattern=mask(msg)[:300], level=level, example=raw.strip()[:500])
        t.count += 1
        if ts:
            t.first_ts = t.first_ts or ts
            t.last_ts = ts
        if source:
            t.sources.add(source)
    rank = {"error": 0, "warning": 1, "info": 2, "debug": 3}
    ordered = sorted(groups.values(), key=lambda t: (rank.get(t.level, 2), -t.count))
    return {
        "lines_examined": total,
        "by_level": by_level,
        "templates": [
            {"level": t.level, "count": t.count, "pattern": t.pattern, "first_seen": t.first_ts,
             "last_seen": t.last_ts, "example": t.example, **({"sources": sorted(t.sources)[:5]} if t.sources else {})}
            for t in ordered[:max_templates]
        ],
        "templates_omitted": max(0, len(ordered) - max_templates),
    }
