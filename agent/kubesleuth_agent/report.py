"""RCA report: facts, hypotheses, evidence, conclusion, uncertainty - kept separate on purpose.

Numbers (posteriors, confidence) and citations come from the ledger; only the
narrative fields (title, root-cause sentence, causal chain wording, remediation)
come from the reasoner.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from . import timeline as tl

CONFIDENCE_TEXT = {
    "high": "High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.",
    "medium": "Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.",
    "low": "Low: the leading explanation is plausible but not demonstrated.",
    "inconclusive": "Inconclusive: no hypothesis is supported well enough to be called the root cause.",
}


def build_report(inv, draft, label: str, posterior: float, top) -> dict:
    post = inv.ledger.posteriors()
    hyps = []
    for h in inv.ledger.hypotheses.values():
        prof = inv.ledger.support_profile(h.id)
        hyps.append({"id": h.id, "statement": h.statement, "mechanism": h.mechanism, "component": h.component,
                     "category": h.category, "layer": h.layer, "status": h.status, "retired_reason": h.retired_reason,
                     "posterior": round(post.get(h.id, 0.0), 3), **prof})
    hyps.sort(key=lambda h: (h["status"] != "active", h["layer"] != "cause", -h["posterior"]))
    evidence = [{"id": e.id, "hypothesis": e.hypothesis_id, "observation": e.observation_id, "source": e.source,
                 "stance": e.stance, "strength": e.strength, "weight": e.weight, "quote": e.quote, "rationale": e.rationale}
                for e in inv.ledger.evidence if e.accepted]
    rejected = [{"hypothesis": e.hypothesis_id, "observation": e.observation_id, "quote": e.quote[:160],
                 "reason": e.reject_reason} for e in inv.ledger.rejected()]
    timeline = [asdict(e) for e in tl.build(inv.store)]
    obs = [{"id": o.id, "round": o.round, "tool": o.tool, "args": o.args, "purpose": o.purpose, "ok": o.ok,
            "source": o.source, "flagged": len(o.suspicious)} for o in inv.store.all()]
    sec = [asdict(e) for e in inv.firewall.events]
    return {
        "id": inv.id,
        "incident": inv.incident,
        "namespace": inv.namespace,
        "reasoner": getattr(inv.reasoner, "name", "?"),
        "started_at": _iso(inv.started), "finished_at": _iso(inv.finished or inv.started),
        "duration_s": round((inv.finished or inv.started) - inv.started, 1),
        "stop_reason": inv.stop_reason,
        "title": draft.title if draft else (f"RCA: {top.statement}" if top else "RCA: inconclusive"),
        "root_cause": {"hypothesis": top.id if top else None,
                       "statement": draft.root_cause if draft else (top.statement if top else None),
                       "component": top.component if top else None, "category": top.category if top else None},
        "confidence": {"label": label, "posterior": round(posterior, 3), "explanation": CONFIDENCE_TEXT[label]},
        "causal_chain": [c.model_dump() for c in draft.causal_chain] if draft else [],
        "facts": [asdict(f) for f in inv.ledger.facts],
        "hypotheses": hyps,
        "evidence": evidence,
        "rejected_evidence": rejected,
        "alternatives": [a.model_dump() for a in draft.alternatives] if draft else [],
        "uncertainty": (draft.uncertainty if draft else []),
        "remediation": (draft.remediation if draft else []),
        "timeline": timeline,
        "security": {"events": sec, "model_notes": inv.security_notes},
        "observations": obs,
        "rounds": [asdict(r) for r in inv.rounds],
        "stats": {"rounds": len([r for r in inv.rounds if r.round > 0]), "tool_calls": inv.total_calls,
                  "evidence_accepted": len(evidence), "evidence_rejected": len(rejected),
                  "llm_usage": getattr(inv.reasoner, "usage", None)},
    }


def _iso(t: float) -> str:
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _q(s: str, n: int = 160) -> str:
    s = " ".join(str(s).split())
    return (s[:n] + "…") if len(s) > n else s


def to_markdown(r: dict) -> str:
    L = []
    w = L.append
    w(f"# {r['title']}\n")
    w(f"**Incident:** {r['incident']}  ")
    w(f"**Namespace:** `{r['namespace']}` · **Investigation:** `{r['id']}` · **Reasoner:** `{r['reasoner']}` · "
      f"{r['stats']['rounds']} rounds, {r['stats']['tool_calls']} tool calls, {r['duration_s']}s\n")

    rc = r["root_cause"]
    w("## Root cause\n")
    w(f"{rc['statement'] or 'Not determined.'}\n")
    if rc["hypothesis"]:
        w(f"*Hypothesis {rc['hypothesis']} · component `{rc['component']}` · category `{rc['category']}`*\n")
    c = r["confidence"]
    w(f"**Confidence: {c['label'].upper()}** (posterior {c['posterior']:.2f}). {c['explanation']}\n")

    if r["causal_chain"]:
        w("## Causal chain\n")
        for i, s in enumerate(r["causal_chain"], 1):
            cites = f" ({', '.join(s['observation_ids'])})" if s["observation_ids"] else ""
            w(f"{i}. {s['step']}{cites}")
        w("")

    top_id = rc["hypothesis"]
    sup = [e for e in r["evidence"] if e["hypothesis"] == top_id]
    if sup:
        w("## Evidence for the conclusion\n")
        w("| | Source | Strength | Verbatim quote | Why it matters |")
        w("|---|---|---|---|---|")
        for e in sup:
            mark = "✅" if e["stance"] == "supports" else "❌"
            w(f"| {mark} {e['observation']} | {e['source']} | {e['strength']} ({e['weight']:+}) | `{_q(e['quote'], 110)}` | {_q(e['rationale'], 140)} |")
        w("")

    if r["timeline"]:
        w("## Timeline\n")
        w("| Time (UTC) | Kind | Event | Obs |")
        w("|---|---|---|---|")
        for t in r["timeline"][:30]:
            w(f"| {t['time']} | {t['kind']} | {_q(t['event'], 150)} | {t['observation_id']} |")
        w("")

    if r["facts"]:
        w("## Observed facts\n")
        for f in r["facts"][:15]:
            w(f"- {f['statement']} — `{_q(f['quote'], 100)}` ({f['observation_id']}, {f['source']})")
        w("")

    w("## Hypotheses considered\n")
    w("| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |")
    w("|---|---|---|---|---|---|---|---|")
    for h in r["hypotheses"]:
        status = h["status"] + (f" ({_q(h['retired_reason'], 60)})" if h["retired_reason"] else "")
        w(f"| {h['id']} | {h['posterior']:.2f} | {h['layer']} | {h['category']} | {status} | +{h['supporting']}/−{h['contradicting']} "
          f"| {', '.join(h['sources'])} | {_q(h['statement'], 120)} |")
    w("")

    if r["alternatives"]:
        w("## Alternative explanations\n")
        for a in r["alternatives"]:
            w(f"- **{a['hypothesis_id']}**: {a['why_less_likely']}")
        w("")
    other = [e for e in r["evidence"] if e["hypothesis"] != top_id]
    if other:
        w("<details><summary>Evidence for/against other hypotheses</summary>\n")
        for e in other:
            w(f"- {e['hypothesis']} {e['stance']} ({e['strength']}, {e['observation']}/{e['source']}): `{_q(e['quote'], 100)}` — {_q(e['rationale'], 120)}")
        w("\n</details>\n")

    w("## Uncertainty\n")
    for u in r["uncertainty"] or ["(none stated)"]:
        w(f"- {u}")
    if r["rejected_evidence"]:
        w(f"- {len(r['rejected_evidence'])} evidence claim(s) were rejected by the grounding check "
          "(quote not found in the cited observation); they did not affect the conclusion.")
    w("")

    if r["remediation"]:
        w("## Suggested remediation (not executed — the agent is read-only)\n")
        for x in r["remediation"]:
            w(f"- {x}")
        w("")

    sec = r["security"]
    w("## Security notes\n")
    if not sec["events"] and not sec["model_notes"]:
        w("- No suspicious data or blocked actions.")
    for e in sec["events"]:
        w(f"- `{e['kind']}`{' in ' + e['observation_id'] if e.get('observation_id') else ''}: {_q(e['detail'], 200)}")
    for n in sec["model_notes"]:
        w(f"- model note: {_q(n, 200)}")
    w("")

    w("<details><summary>Investigation trace</summary>\n")
    for rd in r["rounds"]:
        w(f"**Round {rd['round']}** — decision: {rd['decision'] or '-'}; evidence +{rd['evidence_accepted']} accepted / "
          f"{rd['evidence_rejected']} rejected; new hypotheses {rd['hypotheses_added']}"
          + (f"; retired {rd['hypotheses_retired']}" if rd["hypotheses_retired"] else "") + (f"; notes: {rd['notes']}" if rd["notes"] else ""))
        for call in rd["calls"]:
            args = json.dumps(call["args"]) if isinstance(call["args"], dict) else call["args"]
            status = f"BLOCKED: {call['blocked']}" if call.get("blocked") else (call.get("observation") or "")
            w(f"  - `{call['tool']}` {args} — {call.get('purpose', '')} → {status}")
        if rd["posteriors"]:
            w("  - posteriors: " + ", ".join(f"{k}={v:.2f}" for k, v in rd["posteriors"].items()))
        w("")
    w(f"Stop reason: {r['stop_reason']}\n\n</details>")
    return "\n".join(L)
