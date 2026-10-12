"""Compact, model-friendly summaries of Prometheus series.

Raw matrices are expensive and hard for a model to read. Each series becomes:
stats (first/last/min/max/mean), a unicode sparkline, and an *onset*: the first
time the series departs from its own baseline and stays there. Onsets are what
the agent lines up against deploys and config changes to reason about causality.
"""
from __future__ import annotations

import math
import statistics
from datetime import datetime, timezone

SPARK = "▁▂▃▄▅▆▇█"


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sparkline(values: list[float], width: int = 40) -> str:
    vals = [v for v in values if not math.isnan(v)]
    if not vals:
        return ""
    if len(values) > width:  # downsample by max-pooling (keeps spikes visible)
        step = len(values) / width
        values = [max((v for v in values[int(i * step):int((i + 1) * step)] if not math.isnan(v)), default=float("nan"))
                  for i in range(width)]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    return "".join(" " if math.isnan(v) else SPARK[min(7, int((v - lo) / span * 7.999))] for v in values)


def detect_onset(points: list[tuple[float, float]], min_points: int = 6, sustain: int = 3) -> dict | None:
    """Robust change detection: baseline = first third of the window (median/MAD);
    onset = first point after which `sustain` consecutive points deviate."""
    pts = [(t, v) for t, v in points if not math.isnan(v)]
    if len(pts) < min_points:
        return None
    k = max(3, len(pts) // 3)
    base = [v for _, v in pts[:k]]
    med = statistics.median(base)
    mad = statistics.median([abs(v - med) for v in base]) or 0.0
    scale = max(mad * 1.4826, abs(med) * 0.25, 1e-9)
    threshold = 4.0 * scale
    run = 0
    for i in range(k, len(pts)):
        if abs(pts[i][1] - med) > threshold:
            run += 1
            if run >= sustain:
                j = i - sustain + 1
                direction = "increase" if pts[j][1] > med else "decrease"
                return {"time": iso(pts[j][0]), "direction": direction,
                        "baseline": round(med, 6), "value_after": round(pts[i][1], 6)}
        else:
            run = 0
    return None


def summarize_series(metric: dict, values: list, unit: str = "") -> dict:
    pts = []
    for t, v in values:
        try:
            pts.append((float(t), float(v)))
        except (TypeError, ValueError):
            continue
    vals = [v for _, v in pts if not math.isnan(v)]
    if not vals:
        return {"labels": metric, "points": 0}
    out = {
        "labels": {k: v for k, v in metric.items() if k not in ("__name__", "job", "endpoint", "instance", "prometheus")},
        "points": len(pts),
        "from": iso(pts[0][0]),
        "to": iso(pts[-1][0]),
        "first": _r(vals[0]), "last": _r(vals[-1]), "min": _r(min(vals)), "max": _r(max(vals)),
        "mean": _r(sum(vals) / len(vals)),
        "sparkline": sparkline([v for _, v in pts]),
    }
    if unit:
        out["unit"] = unit
    onset = detect_onset(pts)
    if onset:
        out["onset"] = onset
    return out


def _r(v: float) -> float:
    if v == 0 or math.isnan(v) or math.isinf(v):
        return v
    return round(v, max(2, 3 - int(math.floor(math.log10(abs(v))))))
