"""Score an RCA report against a scenario's known ground truth.

Verdicts
  correct      - names the right component AND (right category OR a mechanism keyword),
                 and does not blame a component that is only a victim/symptom
  partial      - right mechanism or category, but wrong/unclear component, or blames a symptom too
  wrong        - confident about something else
  inconclusive - the agent said it could not decide (better than wrong; scored separately)
"""
from __future__ import annotations


def _text(report: dict) -> str:
    rc = report.get("root_cause") or {}
    parts = [str(rc.get("statement") or ""), str(rc.get("component") or ""), report.get("title", "")]
    parts += [c.get("step", "") for c in report.get("causal_chain", [])]
    return " ".join(parts).lower()


def score(report: dict, gt: dict) -> dict:
    rc = report.get("root_cause") or {}
    comp = str(rc.get("component") or "").lower()
    text = _text(report)
    head = (str(rc.get("statement") or "") + " " + comp).lower()
    components = [c.lower() for c in gt.get("components", [])]
    component_hit = any(c in comp or c in head for c in components)
    category_hit = (rc.get("category") or "") in gt.get("categories", [])
    keywords = [k.lower() for k in gt.get("keywords", [])]
    keyword_hits = [k for k in keywords if k in text]
    blamed_symptom = any(b.lower() == comp.split("/")[-1] for b in gt.get("must_not_blame", []))
    label = (report.get("confidence") or {}).get("label")

    if label == "inconclusive":
        verdict = "inconclusive"
    elif component_hit and (category_hit or keyword_hits) and not blamed_symptom:
        verdict = "correct"
    elif keyword_hits or category_hit:
        verdict = "partial"
    else:
        verdict = "wrong"
    sources = sorted({e["source"] for e in report.get("evidence", []) if e.get("hypothesis") == rc.get("hypothesis")
                      and e.get("stance") == "supports"})
    return {
        "verdict": verdict, "component_hit": component_hit, "category_hit": category_hit,
        "keyword_hits": keyword_hits, "blamed_symptom": blamed_symptom, "confidence": label,
        "posterior": (report.get("confidence") or {}).get("posterior"),
        "evidence_sources": sources, "multi_source": len(sources) >= 2,
        "rounds": report.get("stats", {}).get("rounds"), "tool_calls": report.get("stats", {}).get("tool_calls"),
        "evidence_rejected": report.get("stats", {}).get("evidence_rejected"),
        "security_events": len((report.get("security") or {}).get("events", [])),
        "duration_s": report.get("duration_s"),
        "tokens": (report.get("stats", {}).get("llm_usage") or {}).get("input_tokens", 0)
                  + (report.get("stats", {}).get("llm_usage") or {}).get("output_tokens", 0),
    }
