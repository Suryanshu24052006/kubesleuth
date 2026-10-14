"""Score an RCA report against a scenario's known ground truth.

Only the agent's actual conclusion counts: the root-cause statement and the component of the winning
hypothesis. Words that appear elsewhere in the report (causal chain, alternatives) do not.

Verdicts
  correct      - names the right component AND the actual mechanism (ground_truth.mechanism),
                 and the winning hypothesis does not blame a victim (ground_truth.must_not_blame)
  partial      - on the right track: the mechanism, a related keyword, or the right component,
                 but not the full cause (for example the right mechanism with a victim crowned)
  wrong        - a confident conclusion about something else
  inconclusive - the agent said it could not decide (better than wrong; reported separately)
"""
from __future__ import annotations


def score(report: dict, gt: dict) -> dict:
    rc = report.get("root_cause") or {}
    comp = str(rc.get("component") or "").lower()
    head = (str(rc.get("statement") or "") + " " + comp).lower()
    components = [c.lower() for c in gt.get("components", [])]
    mechanism = [m.lower() for m in gt.get("mechanism", gt.get("keywords", []))]
    hints = [k.lower() for k in gt.get("keywords", [])]

    component_hit = any(c in head for c in components)
    mechanism_hit = any(m in head for m in mechanism)
    hint_hits = [k for k in hints if k in head]
    blamed_victim = comp.split("/")[-1] in [b.lower() for b in gt.get("must_not_blame", [])]
    label = (report.get("confidence") or {}).get("label")

    if label == "inconclusive":
        verdict = "inconclusive"
    elif component_hit and mechanism_hit and not blamed_victim:
        verdict = "correct"
    elif mechanism_hit or hint_hits or (component_hit and not blamed_victim):
        verdict = "partial"
    else:
        verdict = "wrong"
    sources = sorted({e["source"] for e in report.get("evidence", []) if e.get("hypothesis") == rc.get("hypothesis")
                      and e.get("stance") == "supports"})
    usage = report.get("stats", {}).get("llm_usage") or {}
    return {
        "verdict": verdict, "component_hit": component_hit, "mechanism_hit": mechanism_hit,
        "keyword_hits": hint_hits, "blamed_victim": blamed_victim,
        "category_hit": (rc.get("category") or "") in gt.get("categories", []), "confidence": label,
        "posterior": (report.get("confidence") or {}).get("posterior"),
        "evidence_sources": sources, "multi_source": len(sources) >= 2,
        "rounds": report.get("stats", {}).get("rounds"), "tool_calls": report.get("stats", {}).get("tool_calls"),
        "evidence_rejected": report.get("stats", {}).get("evidence_rejected"),
        "security_events": len((report.get("security") or {}).get("events", [])),
        "duration_s": report.get("duration_s"),
        "tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
    }
