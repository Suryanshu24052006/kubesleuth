"""Hypothesis ledger: explicit, auditable belief state for the investigation.

The language model proposes hypotheses and grades evidence; *this code* decides
how much that evidence counts. Each accepted evidence item shifts a hypothesis'
log-odds score by a fixed weight. Posteriors are a softmax over the competing
hypotheses plus an "unexplained" alternative, so the agent can never be certain
of a story it has barely tested, and confidence comes from evidence, not from
the model's self-report.

Guards:
  * grounding  - evidence must cite an existing observation and quote it verbatim;
  * double counting - one (hypothesis, observation) pair counts once;
  * source diversity - repeated evidence from the same source decays geometrically;
  * symptoms can be tracked but never be concluded as root cause.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

from .observations import ObservationStore, normalize_for_match

Category = Literal["deployment", "configuration", "resource_exhaustion", "dependency", "capacity",
                   "networking", "probe_misconfiguration", "code_defect", "version_skew", "external", "other"]

WEIGHTS = {"weak": 0.5, "moderate": 1.2, "strong": 2.3}
SOURCE_DECAY = 0.6
UNEXPLAINED_SCORE = 1.0  # log-odds mass reserved for "none of the above"


@dataclass
class Hypothesis:
    id: str
    statement: str
    mechanism: str
    component: str
    category: str
    layer: Literal["cause", "symptom"] = "cause"
    predictions: list[str] = field(default_factory=list)
    status: Literal["active", "retired"] = "active"
    retired_reason: str = ""
    created_round: int = 0


@dataclass
class Evidence:
    id: str
    hypothesis_id: str
    observation_id: str
    quote: str
    stance: Literal["supports", "contradicts"]
    strength: Literal["weak", "moderate", "strong"]
    rationale: str
    source: str = ""
    accepted: bool = True
    reject_reason: str = ""
    weight: float = 0.0
    round: int = 0


@dataclass
class Fact:
    observation_id: str
    quote: str
    statement: str
    time: str | None = None
    source: str = ""


class Ledger:
    def __init__(self, store: ObservationStore):
        self.store = store
        self.hypotheses: dict[str, Hypothesis] = {}
        self.evidence: list[Evidence] = []
        self.facts: list[Fact] = []
        self._ev_seq = 0

    # ---------------------------------------------------------------- hypotheses
    def add_hypothesis(self, statement: str, mechanism: str, component: str, category: str, layer: str = "cause",
                       predictions: list[str] | None = None, round_: int = 0) -> Hypothesis:
        key = (component.strip().lower(), category)
        for h in self.hypotheses.values():
            if h.status == "active" and (h.component.strip().lower(), h.category) == key and \
                    _similar(h.statement, statement):
                return h  # same idea re-proposed: keep the original id and evidence
        hid = f"H{len(self.hypotheses) + 1}"
        h = Hypothesis(hid, statement.strip(), mechanism.strip(), component.strip(), category,
                       layer if layer in ("cause", "symptom") else "cause", predictions or [], created_round=round_)
        self.hypotheses[hid] = h
        return h

    def retire(self, hid: str, reason: str) -> None:
        h = self.hypotheses.get(hid)
        if h and h.status == "active":
            h.status, h.retired_reason = "retired", reason

    def active(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.status == "active"]

    # ---------------------------------------------------------------- facts & evidence
    def verify_quote(self, observation_id: str, quote: str) -> tuple[bool, str]:
        obs = self.store.get(observation_id)
        if obs is None:
            return False, f"unknown observation {observation_id}"
        q = normalize_for_match(quote or "")
        if len(q) < 8:
            return False, "quote too short to verify"
        if q not in normalize_for_match(obs.text):
            return False, "quote not found verbatim in the cited observation"
        return True, ""

    def add_fact(self, observation_id: str, quote: str, statement: str, time: str | None = None) -> bool:
        ok, _ = self.verify_quote(observation_id, quote)
        if ok:
            obs = self.store.get(observation_id)
            self.facts.append(Fact(observation_id, quote, statement, time, obs.source if obs else ""))
        return ok

    def add_evidence(self, hypothesis_id: str, observation_id: str, quote: str, stance: str, strength: str,
                     rationale: str, round_: int = 0) -> Evidence:
        self._ev_seq += 1
        obs = self.store.get(observation_id)
        ev = Evidence(f"E{self._ev_seq}", hypothesis_id, observation_id, quote, stance, strength, rationale,
                      source=obs.source if obs else "", round=round_)
        h = self.hypotheses.get(hypothesis_id)
        if h is None:
            ev.accepted, ev.reject_reason = False, f"unknown hypothesis {hypothesis_id}"
        elif stance not in ("supports", "contradicts") or strength not in WEIGHTS:
            ev.accepted, ev.reject_reason = False, "invalid stance/strength"
        else:
            ok, why = self.verify_quote(observation_id, quote)
            if not ok:
                ev.accepted, ev.reject_reason = False, why
            elif any(e.accepted and e.hypothesis_id == hypothesis_id and e.observation_id == observation_id
                     and e.stance == stance for e in self.evidence):
                ev.accepted, ev.reject_reason = False, "duplicate: this observation already counted for this hypothesis"
        self.evidence.append(ev)
        return ev

    # ---------------------------------------------------------------- scoring
    def score(self, hid: str) -> float:
        per_source: dict[tuple[str, str], int] = {}
        total = 0.0
        for e in self.evidence:
            if not e.accepted or e.hypothesis_id != hid:
                continue
            k = (e.source, e.stance)
            n = per_source.get(k, 0)
            per_source[k] = n + 1
            w = WEIGHTS[e.strength] * (SOURCE_DECAY ** n)
            e.weight = round(w if e.stance == "supports" else -w, 3)
            total += e.weight
        return total

    def posteriors(self) -> dict[str, float]:
        scores = {h.id: self.score(h.id) for h in self.active()}
        scores["unexplained"] = UNEXPLAINED_SCORE
        m = max(scores.values())
        exp = {k: math.exp(v - m) for k, v in scores.items()}
        z = sum(exp.values())
        return {k: v / z for k, v in exp.items()}

    def ranked(self, causes_only: bool = True) -> list[tuple[Hypothesis, float]]:
        post = self.posteriors()
        hs = [(h, post.get(h.id, 0.0)) for h in self.active() if not causes_only or h.layer == "cause"]
        return sorted(hs, key=lambda x: -x[1])

    def support_profile(self, hid: str) -> dict:
        ev = [e for e in self.evidence if e.accepted and e.hypothesis_id == hid]
        sup = [e for e in ev if e.stance == "supports"]
        con = [e for e in ev if e.stance == "contradicts"]
        return {"supporting": len(sup), "contradicting": len(con),
                "sources": sorted({e.source for e in sup}),
                "strong_contradictions": sum(1 for e in con if e.strength == "strong")}

    def confidence(self) -> tuple[str, float, Hypothesis | None]:
        ranked = self.ranked()
        if not ranked:
            return "inconclusive", 0.0, None
        top, p = ranked[0]
        prof = self.support_profile(top.id)
        runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
        if p >= 0.80 and len(prof["sources"]) >= 2 and prof["supporting"] >= 3 and not prof["strong_contradictions"] \
                and p - runner_up >= 0.35:
            return "high", p, top
        if p >= 0.55 and prof["supporting"] >= 2:
            return "medium", p, top
        if p >= 0.35:
            return "low", p, top
        return "inconclusive", p, top

    def rejected(self) -> list[Evidence]:
        return [e for e in self.evidence if not e.accepted]

    # ---------------------------------------------------------------- rendering for prompts
    def render(self) -> str:
        if not self.hypotheses:
            return "(no hypotheses yet)"
        post = self.posteriors()
        lines = []
        for h in self.hypotheses.values():
            prof = self.support_profile(h.id)
            if h.status == "retired":
                lines.append(f"{h.id} [RETIRED: {h.retired_reason}] {h.statement}")
                continue
            lines.append(f"{h.id} p={post.get(h.id, 0):.2f} layer={h.layer} category={h.category} component={h.component} "
                         f"(+{prof['supporting']}/-{prof['contradicting']}, sources={prof['sources']}): {h.statement}\n"
                         f"    mechanism: {h.mechanism}\n"
                         f"    predictions: {'; '.join(h.predictions[:4])}")
        lines.append(f"(unexplained / none of the above) p={post['unexplained']:.2f}")
        return "\n".join(lines)


def _similar(a: str, b: str) -> bool:
    ta, tb = set(normalize_for_match(a).split()), set(normalize_for_match(b).split())
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= 0.6
