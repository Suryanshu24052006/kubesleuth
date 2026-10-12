"""The investigation loop as an explicit LangGraph state machine.

   triage ─► hypothesize ─► plan ─► act ─► assess ─► decide ─┬─► hypothesize (loop)
   (fixed,                 (LLM)   (tools  (LLM +    (code)   └─► report ─► END
    no LLM)                         via     verified
                                    MCP)    ledger)

* triage is deterministic: the first look is always the same cheap, broad sweep.
* the model chooses tools (plan) and interprets data (assess / hypothesize);
* code owns everything that must be trustworthy: the tool firewall, quote verification,
  posterior computation, the stopping rule and the confidence label.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from . import timeline as tl
from .ledger import Ledger
from .observations import Observation, ObservationStore
from .reasoners import Context, Reasoner
from .toolclient import BrokerClient, Firewall, SecurityEvent

log = logging.getLogger("kubesleuth.investigation")


@dataclass
class Budget:
    max_rounds: int = 6
    max_calls_per_round: int = 4
    max_total_calls: int = 26
    confident_posterior: float = 0.80
    confident_margin: float = 0.35


@dataclass
class RoundLog:
    round: int
    hypotheses_added: list[str] = field(default_factory=list)
    hypotheses_retired: list[str] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)
    evidence_accepted: int = 0
    evidence_rejected: int = 0
    posteriors: dict = field(default_factory=dict)
    decision: str = ""
    notes: str = ""


class GraphState(TypedDict, total=False):
    round: int
    stalls: int
    done: bool
    stop_reason: str


class Investigation:
    def __init__(self, incident: str, namespace: str, broker: BrokerClient, reasoner: Reasoner,
                 budget: Budget | None = None, on_event: Callable[[str, dict], None] | None = None):
        self.id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        self.incident = incident
        self.namespace = namespace
        self.broker = broker
        self.reasoner = reasoner
        self.budget = budget or Budget()
        self.store = ObservationStore()
        self.ledger = Ledger(self.store)
        self.firewall = Firewall(broker.read_only_tool_names, namespace)
        self.rounds: list[RoundLog] = []
        self.security_notes: list[str] = []
        self.total_calls = 0
        self.started = time.time()
        self.finished: float | None = None
        self.stop_reason = ""
        self.report = None
        self._emit = on_event or (lambda kind, payload: None)
        self._pending: list[Observation] = []
        self._revisit: list[Observation] = []
        self._model_says_done = False

    # ------------------------------------------------------------------ helpers
    def ctx(self, round_: int, stalled: bool = False) -> Context:
        return Context(incident=self.incident, namespace=self.namespace, round=round_,
                       max_rounds=self.budget.max_rounds, max_calls=self.budget.max_calls_per_round,
                       ledger=self.ledger, store=self.store, timeline=tl.render(tl.build(self.store)),
                       tools=[t for t in self.broker.tools if t["name"] in self.firewall.allowed_tools],
                       stalled=stalled, new_observations=list(self._pending),
                       revisit_observations=list(self._revisit))

    def _round(self, n: int) -> RoundLog:
        while len(self.rounds) <= n:
            self.rounds.append(RoundLog(len(self.rounds)))
        return self.rounds[n]

    async def _call(self, tool: str, args: dict, purpose: str, round_: int) -> Observation:
        prior = self.store.seen_call(tool, args)
        if prior:
            return prior
        ok, text = await self.broker.call(tool, args)
        self.total_calls += 1
        obs = self.store.add(tool, args, purpose, ok, text, round_)
        if obs.suspicious:
            for s in obs.suspicious[:3]:
                self.firewall.events.append(SecurityEvent(
                    "suspicious_data", f"{s.get('pattern')}: {s.get('excerpt', '')[:160]}", round_, obs.id))
        self._round(round_).calls.append({"observation": obs.id, "tool": tool, "args": args, "purpose": purpose,
                                          "ok": ok})
        self._emit("observation", {"id": obs.id, "tool": tool, "args": args, "ok": ok, "purpose": purpose})
        return obs

    def _apply_hypotheses(self, drafts, round_: int):
        for d in drafts:
            before = len(self.ledger.hypotheses)
            h = self.ledger.add_hypothesis(d.statement, d.mechanism, d.component, d.category, d.layer,
                                           d.predictions, round_)
            if len(self.ledger.hypotheses) > before:
                self._round(round_).hypotheses_added.append(h.id)
                self._emit("hypothesis", {"id": h.id, "statement": h.statement, "layer": h.layer})

    # ------------------------------------------------------------------ graph nodes
    async def triage(self, state: GraphState) -> GraphState:
        ns = self.namespace
        calls = [("active_alerts", {}, "what is alerting and since when"),
                 ("cluster_overview", {"namespace": ns}, "resource-level health snapshot"),
                 ("recent_changes", {"namespace": ns, "minutes": 120}, "what changed recently"),
                 ("get_events", {"namespace": ns, "minutes": 60, "warnings_only": True}, "recent warning events")]
        self._pending = list(await asyncio.gather(*(self._call(t, a, p, 0) for t, a, p in calls)))
        try:
            assessment = await self.reasoner.assess(self.ctx(0))
            self._apply_assessment(assessment, 0)
        except Exception as exc:
            log.warning("triage assessment failed: %s", exc)
        return {"round": 1, "stalls": 0, "done": False}

    async def hypothesize(self, state: GraphState) -> GraphState:
        r = state["round"]
        try:
            upd = await self.reasoner.hypothesize(self.ctx(r, stalled=state.get("stalls", 0) > 0))
        except Exception as exc:
            self._round(r).notes += f"hypothesize failed: {exc}. "
            return {}
        self._apply_hypotheses(upd.new_hypotheses, r)
        for ret in upd.retire:
            if ret.hypothesis_id in self.ledger.hypotheses:
                self.ledger.retire(ret.hypothesis_id, ret.reason)
                self._round(r).hypotheses_retired.append(ret.hypothesis_id)
        return {}

    async def plan_and_act(self, state: GraphState) -> GraphState:
        r = state["round"]
        remaining = self.budget.max_total_calls - self.total_calls
        self._pending = []
        if remaining <= 0:
            return {}
        try:
            plan = await self.reasoner.plan(self.ctx(r))
        except Exception as exc:
            self._round(r).notes += f"plan failed: {exc}. "
            return {}
        self._model_says_done = plan.enough_evidence
        approved = []
        for c in plan.calls[: min(self.budget.max_calls_per_round, remaining)]:
            ok, args, why = self.firewall.check(c.tool, c.args_json, r)
            if not ok:
                self._round(r).calls.append({"tool": c.tool, "args": c.args_json[:200], "purpose": c.purpose,
                                             "blocked": why})
                self._emit("blocked", {"tool": c.tool, "reason": why})
                continue
            if self.store.seen_call(c.tool, args):
                continue
            approved.append((c.tool, args, c.purpose))
        self._pending = list(await asyncio.gather(*(self._call(t, a, p, r) for t, a, p in approved)))
        # Hypotheses born this round have never been tested against earlier data: let the
        # assessor re-read the most informative earlier observations (compactly).
        self._revisit = []
        if self._round(r).hypotheses_added:
            earlier = [o for o in self.store.all() if o not in self._pending and o.ok]
            triage = [o for o in earlier if o.round == 0]
            recent = [o for o in earlier if o.round > 0][-6:]
            self._revisit = triage + recent
        return {}

    def _apply_assessment(self, a, r: int) -> None:
        for f in a.facts:
            self.ledger.add_fact(f.observation_id, f.quote, f.statement, f.time)
        rl = self._round(r)
        for e in a.evidence:
            ev = self.ledger.add_evidence(e.hypothesis_id, e.observation_id, e.quote, e.stance, e.strength,
                                          e.rationale, r)
            if ev.accepted:
                rl.evidence_accepted += 1
            else:
                rl.evidence_rejected += 1
        self._apply_hypotheses(a.new_hypotheses, r)
        self.security_notes += [n for n in a.security_notes if n not in self.security_notes]

    async def assess(self, state: GraphState) -> GraphState:
        r = state["round"]
        if not self._pending and not self._revisit:
            return {}
        try:
            self._apply_assessment(await self.reasoner.assess(self.ctx(r)), r)
        except Exception as exc:
            self._round(r).notes += f"assess failed: {exc}. "
        return {}

    async def decide(self, state: GraphState) -> GraphState:
        r = state["round"]
        rl = self._round(r)
        rl.posteriors = {k: round(v, 3) for k, v in self.ledger.posteriors().items()}
        ranked = self.ledger.ranked()
        stalls = state.get("stalls", 0)
        stalls = stalls + 1 if (rl.evidence_accepted == 0 and not rl.hypotheses_added) else 0

        reason = ""
        label, p, top = self.ledger.confidence()
        if top is not None:
            runner = ranked[1][1] if len(ranked) > 1 else 0.0
            if label == "high" and p - runner >= self.budget.confident_margin:
                prof = self.ledger.support_profile(top.id)
                reason = f"confident: {top.id} p={p:.2f}, margin {p - runner:.2f}, sources {prof['sources']}"
            elif self._model_says_done and label in ("high", "medium") and r >= 2:
                reason = f"model judged evidence sufficient; {top.id} p={p:.2f} ({label})"
        if not reason and r >= self.budget.max_rounds:
            reason = "round budget exhausted"
        if not reason and self.total_calls >= self.budget.max_total_calls:
            reason = "tool-call budget exhausted"
        if not reason and stalls >= 2:
            reason = "no new evidence for two rounds"
        rl.decision = reason or "continue"
        self._emit("round", {"round": r, "posteriors": rl.posteriors, "decision": rl.decision})
        if reason:
            return {"done": True, "stop_reason": reason, "stalls": stalls}
        return {"round": r + 1, "stalls": stalls}

    async def write_report(self, state: GraphState) -> GraphState:
        from .report import build_report
        self.stop_reason = state.get("stop_reason", "")
        label, p, top = self.ledger.confidence()
        try:
            draft = await self.reasoner.report(self.ctx(state.get("round", 0)), label, p, top.id if top else None)
        except Exception as exc:
            draft = None
            self.security_notes.append(f"(report narrative unavailable: {exc})")
        self.finished = time.time()
        self.report = build_report(self, draft, label, p, top)
        return {}

    # ------------------------------------------------------------------ graph
    def graph(self):
        g = StateGraph(GraphState)
        g.add_node("triage", self.triage)
        g.add_node("hypothesize", self.hypothesize)
        g.add_node("plan_and_act", self.plan_and_act)
        g.add_node("assess", self.assess)
        g.add_node("decide", self.decide)
        g.add_node("report", self.write_report)
        g.add_edge(START, "triage")
        g.add_edge("triage", "hypothesize")
        g.add_edge("hypothesize", "plan_and_act")
        g.add_edge("plan_and_act", "assess")
        g.add_edge("assess", "decide")
        g.add_conditional_edges("decide", lambda s: "report" if s.get("done") else "hypothesize",
                                {"report": "report", "hypothesize": "hypothesize"})
        g.add_edge("report", END)
        return g.compile()

    async def run(self):
        await self.graph().ainvoke({"round": 0}, {"recursion_limit": 8 * (self.budget.max_rounds + 2)})
        return self.report
