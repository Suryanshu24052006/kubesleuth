"""Reasoners decide *what to think*; the graph decides *what happens*.

LLMReasoner   - any LangChain chat model (Anthropic, Gemini, OpenAI, Ollama...) with structured output.
RuleReasoner  - deterministic SRE heuristics; a no-API-key baseline used for the offline demo and as an
                eval baseline ("does the LLM beat rules?").
ScriptedReasoner (tests) replays canned outputs, including a deliberately *compromised* model.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from . import prompts
from .ledger import Ledger
from .observations import Observation, ObservationStore
from .schemas import (Assessment, ChainStep, EvidenceDraft, FactDraft, HypothesisDraft, HypothesisUpdate, Plan,
                      ReportDraft, ToolCallPlan)

log = logging.getLogger("kubesleuth.reasoner")


@dataclass
class Context:
    incident: str
    namespace: str
    round: int
    max_rounds: int
    max_calls: int
    ledger: Ledger
    store: ObservationStore
    timeline: str
    tools: list[dict]
    stalled: bool = False
    new_observations: list[Observation] = field(default_factory=list)
    revisit_observations: list[Observation] = field(default_factory=list)


class Reasoner(Protocol):
    name: str
    async def hypothesize(self, ctx: Context) -> HypothesisUpdate: ...
    async def plan(self, ctx: Context) -> Plan: ...
    async def assess(self, ctx: Context) -> Assessment: ...
    async def report(self, ctx: Context, confidence: str, posterior: float, top_id: str | None) -> ReportDraft: ...


def tools_for_prompt(tools: list[dict]) -> str:
    out = []
    for t in tools:
        props = (t.get("input_schema") or {}).get("properties", {})
        req = set((t.get("input_schema") or {}).get("required", []))
        args = []
        for k, v in props.items():
            typ = v.get("type") or "/".join(x.get("type", "?") for x in v.get("anyOf", []))
            args.append(f"{k}{'' if k in req else '?'}:{typ}" + (f"={v['default']}" if "default" in v and v["default"] is not None else ""))
        out.append(f"- {t['name']}({', '.join(args)}): {t.get('description', '')}")
    return "\n".join(out)


def evidence_text(ledger: Ledger) -> str:
    lines = []
    for e in ledger.evidence:
        if e.accepted:
            lines.append(f"{e.id} {e.hypothesis_id} {e.stance} ({e.strength}, {e.source}, {e.observation_id}): "
                         f"\"{e.quote}\" - {e.rationale}")
    return "\n".join(lines) or "(none)"


# ============================================================================ LLM
class LLMReasoner:
    def __init__(self, model_spec: str, temperature: float = 0.0, max_tokens: int = 4096):
        from langchain.chat_models import init_chat_model
        self.name = f"llm:{model_spec}"
        self.model = init_chat_model(model_spec, temperature=temperature, max_tokens=max_tokens)
        self.usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0}

    async def _structured(self, schema, prompt: str):
        runnable = self.model.with_structured_output(schema, include_raw=True)
        last: Exception | None = None
        for attempt in range(2):
            try:
                res = await runnable.ainvoke([("system", prompts.SYSTEM), ("human", prompt)])
                self.usage["calls"] += 1
                um = getattr(res.get("raw"), "usage_metadata", None) or {}
                self.usage["input_tokens"] += um.get("input_tokens", 0)
                self.usage["output_tokens"] += um.get("output_tokens", 0)
                if res.get("parsed") is not None:
                    return res["parsed"]
                last = res.get("parsing_error") or ValueError("no structured output")
            except Exception as exc:  # provider hiccup or malformed output: retry once
                last = exc
            log.warning("structured output attempt %d failed: %s", attempt + 1, last)
        raise RuntimeError(f"model failed to produce {schema.__name__}: {last}")

    async def hypothesize(self, ctx: Context) -> HypothesisUpdate:
        note = ("\nNOTE: the last rounds produced no new verified evidence. Broaden: consider mechanisms you have "
                "not yet considered, or other components.\n") if ctx.stalled else ""
        return await self._structured(HypothesisUpdate, prompts.HYPOTHESIZE.format(
            incident=ctx.incident, namespace=ctx.namespace, round=ctx.round, max_rounds=ctx.max_rounds,
            ledger=ctx.ledger.render(), digest=ctx.store.digest() or "(none)", timeline=ctx.timeline or "(none)",
            stall_note=note))

    async def plan(self, ctx: Context) -> Plan:
        return await self._structured(Plan, prompts.PLAN.format(
            incident=ctx.incident, namespace=ctx.namespace, round=ctx.round, max_rounds=ctx.max_rounds,
            max_calls=ctx.max_calls, ledger=ctx.ledger.render(), digest=ctx.store.digest() or "(none)",
            tools=tools_for_prompt(ctx.tools)))

    async def assess(self, ctx: Context) -> Assessment:
        rendered = "\n\n".join(ctx.store.render(o) for o in ctx.new_observations) or "(none)"
        if ctx.revisit_observations:
            rendered += ("\n\nEarlier observations, re-shown (truncated) because new hypotheses were added; "
                         "assess them against the NEW hypotheses:\n\n"
                         + "\n\n".join(ctx.store.render(o, max_chars=3500) for o in ctx.revisit_observations))
        return await self._structured(Assessment, prompts.ASSESS.format(
            incident=ctx.incident, ledger=ctx.ledger.render(), observations=rendered))

    async def report(self, ctx: Context, confidence: str, posterior: float, top_id: str | None) -> ReportDraft:
        top = ctx.ledger.hypotheses.get(top_id) if top_id else None
        return await self._structured(ReportDraft, prompts.REPORT.format(
            incident=ctx.incident, namespace=ctx.namespace, ledger=ctx.ledger.render(),
            top=f"{top.id}: {top.statement}" if top else "none", posterior=posterior, confidence=confidence,
            evidence=evidence_text(ctx.ledger), timeline=ctx.timeline or "(none)", digest=ctx.store.digest()))


# ============================================================================ rules baseline
VOCAB = {
    "configuration": ["too many clients", "connection", "pool", "reloaded", "configuration"],
    "resource_exhaustion": ["oomkilled", "memory", "buffered", "out of memory"],
    "capacity": ["timeout", "throttl", "scaled down", "upstream timeout", "deadline"],
    "probe_misconfiguration": ["liveness probe failed", "will be restarted", "deadline exceeded", "unhealthy"],
    "dependency": ["connection refused", "connecterror", "name or service not known", "no ready endpoints",
                   "matches no pods", "upstream connection error"],
    "version_skew": ["powerpeg", "legacy", "different workloads"],
    "deployment": ["traceback", "exception", "error", "new-revision"],
}


class RuleReasoner:
    """Deterministic baseline: classic runbook heuristics with grounded quotes."""
    name = "rules"

    async def hypothesize(self, ctx: Context) -> HypothesisUpdate:
        drafts: list[HypothesisDraft] = []
        for o in ctx.store.all():
            d = o.envelope.get("data") or {}
            if o.tool == "recent_changes":
                for c in d.get("changes", []):
                    fields = ", ".join(f"{f['field']} {f.get('old')}->{f.get('new')}" for f in c.get("fields", [])[:3])
                    kind, name = c["kind"], c["name"]
                    fl = fields.lower()
                    if kind == "configmap" and c["change"] == "modified":
                        drafts.append(HypothesisDraft(statement=f"ConfigMap {name} change ({fields}) broke a dependent service",
                                                      mechanism="config pushed then picked up by workloads", component=f"configmap/{name}",
                                                      category="configuration", layer="cause",
                                                      predictions=[f"errors begin after {c['time']}"]))
                    elif kind == "deployment" and "spec.replicas" in fl and _decreased(c):
                        drafts.append(HypothesisDraft(statement=f"Capacity of {name} was reduced ({fields})", mechanism="fewer replicas saturate",
                                                      component=name, category="capacity", layer="cause"))
                    elif kind == "deployment" and "probe" in fl:
                        drafts.append(HypothesisDraft(statement=f"Probe change on {name} ({fields}) kills or unreadies healthy pods",
                                                      mechanism="kubelet restarts containers", component=name,
                                                      category="probe_misconfiguration", layer="cause"))
                    elif kind == "service" and c["change"] in ("modified", "deleted"):
                        drafts.append(HypothesisDraft(statement=f"Service {name} was {c['change']} ({fields}) so callers cannot reach it",
                                                      mechanism="no endpoints / DNS", component=name, category="dependency", layer="cause"))
                    elif kind == "rollout" and any("image" in f["field"] for f in c.get("fields", [])):
                        drafts.append(HypothesisDraft(statement=f"New rollout of {name} ({fields}) introduced a defect",
                                                      mechanism="bad build", component=name, category="deployment", layer="cause"))
                    elif kind == "deployment" and c["change"] == "created":
                        drafts.append(HypothesisDraft(statement=f"Newly created workload {name} serves traffic with different code",
                                                      mechanism="version skew", component=name, category="version_skew", layer="cause"))
            if o.tool == "cluster_overview":
                for f in d.get("findings", []):
                    m = re.match(r"pod (\S+) container (\S+) was OOMKilled", f)
                    if m:
                        drafts.append(HypothesisDraft(statement=f"{m.group(2)} runs out of memory (OOMKilled)", mechanism="memory growth to limit",
                                                      component=m.group(2), category="resource_exhaustion", layer="cause"))
                    m = re.match(r"service (\S+) (selector .* matches NO pods|has 0 ready endpoints)", f)
                    if m:
                        drafts.append(HypothesisDraft(statement=f"Service {m.group(1)} has no healthy backends", mechanism="dependency unavailable",
                                                      component=m.group(1), category="dependency", layer="cause"))
                    m = re.match(r"service (\S+) routes to \d+ different workloads", f)
                    if m:
                        drafts.append(HypothesisDraft(statement=f"Service {m.group(1)} mixes versions of its backend", mechanism="version skew",
                                                      component=m.group(1), category="version_skew", layer="cause"))
        existing = {(h.component, h.category) for h in ctx.ledger.hypotheses.values()}
        drafts = [d for d in drafts if (d.component, d.category) not in existing]
        if not ctx.ledger.hypotheses and not drafts:
            drafts.append(HypothesisDraft(statement="A downstream dependency of the alerting service is failing",
                                          mechanism="errors propagate upstream", component="unknown", category="dependency",
                                          layer="cause"))
        return HypothesisUpdate(new_hypotheses=drafts[:5])

    async def plan(self, ctx: Context) -> Plan:
        ns = ctx.namespace
        alert_svc = _alert_service(ctx.store) or "edge"
        origin = _trace_origin(ctx.store)
        wanted: list[tuple[str, dict, str]] = [
            ("find_traces", {"service": alert_svc, "minutes": 15}, "where do errors originate?"),
            ("get_events", {"namespace": ns, "minutes": 60, "warnings_only": True}, "recent warnings"),
        ]
        if origin:
            wanted += [("search_logs", {"namespace": ns, "app": origin, "level": "error", "minutes": 30}, f"errors in {origin}"),
                       ("workload_metrics", {"namespace": ns, "workload": origin, "minutes": 30}, f"golden signals of {origin}")]
        wanted.append(("workload_metrics", {"namespace": ns, "workload": alert_svc, "minutes": 30}, "symptom onset"))
        for h in ctx.ledger.active():
            if "/" not in h.component and h.component not in ("unknown",):
                wanted.append(("workload_metrics", {"namespace": ns, "workload": h.component, "minutes": 30}, f"test {h.id}"))
        calls = [ToolCallPlan(tool=t, args_json=json.dumps(a), purpose=p) for t, a, p in wanted
                 if not ctx.store.seen_call(t, a)][:ctx.max_calls]
        return Plan(calls=calls, enough_evidence=not calls)

    async def assess(self, ctx: Context) -> Assessment:
        ev, facts = [], []
        for o in ctx.new_observations + ctx.revisit_observations:
            if not o.ok:
                continue
            text_l = o.text.lower()
            for h in ctx.ledger.active():
                comp = h.component.split("/")[-1].lower()
                for kw in VOCAB.get(h.category, []):
                    i = text_l.find(kw)
                    if i < 0:
                        continue
                    quote = o.text[max(0, i - 40): i + len(kw) + 60]
                    near_comp = comp and comp in text_l[max(0, i - 400): i + 400]
                    ev.append(EvidenceDraft(hypothesis_id=h.id, observation_id=o.id, quote=quote,
                                            stance="supports", strength="moderate" if near_comp else "weak",
                                            rationale=f"'{kw}' observed{' near ' + comp if near_comp else ''}"))
                    break
            d = o.envelope.get("data") or {}
            for name, series in (d.get("signals") or {}).items():
                for s in series:
                    if s.get("onset") and name in ("error_ratio_5xx", "db_errors_rps", "memory_working_set_bytes"):
                        facts.append(FactDraft(observation_id=o.id, quote=s["onset"]["time"],
                                               statement=f"{d.get('workload')} {name} {s['onset']['direction']} at {s['onset']['time']}",
                                               time=s["onset"]["time"]))
        return Assessment(facts=facts[:8], evidence=ev)

    async def report(self, ctx: Context, confidence: str, posterior: float, top_id: str | None) -> ReportDraft:
        top = ctx.ledger.hypotheses.get(top_id) if top_id else None
        sup = [e for e in ctx.ledger.evidence if e.accepted and top and e.hypothesis_id == top.id]
        return ReportDraft(
            title=f"RCA: {top.statement if top else 'inconclusive'}",
            root_cause=top.statement if top else "No hypothesis is supported well enough.",
            causal_chain=[ChainStep(step=e.rationale + f": {e.quote[:80]}", observation_ids=[e.observation_id]) for e in sup[:5]],
            uncertainty=["Baseline rule reasoner: causal links are keyword-based, verify manually."],
            remediation=["Review and revert the implicated change if confirmed."] if top else [])


def _decreased(change: dict) -> bool:
    for f in change.get("fields", []):
        if f["field"] == "spec.replicas":
            try:
                return int(f["new"]) < int(f["old"])
            except (TypeError, ValueError):
                return False
    return False


def _alert_service(store: ObservationStore) -> str | None:
    for o in store.all():
        if o.tool == "active_alerts":
            for a in (o.envelope.get("data") or {}).get("alerts", []):
                svc = (a.get("labels") or {}).get("service")
                if svc:
                    return svc
    return None


def _trace_origin(store: ObservationStore) -> str | None:
    for o in reversed(store.all()):
        if o.tool == "find_traces":
            origins = (o.envelope.get("data") or {}).get("error_origins") or []
            if origins:
                return origins[0]["service"]
    return None


# ============================================================================ scripted (tests)
class ScriptedReasoner:
    """Replays queued outputs; a callable entry is invoked with the context."""
    name = "scripted"

    def __init__(self, script: dict[str, list[Any]]):
        self.script = {k: list(v) for k, v in script.items()}

    def _next(self, kind, ctx, default):
        q = self.script.get(kind) or []
        if not q:
            return default
        item = q.pop(0)
        return item(ctx) if callable(item) else item

    async def hypothesize(self, ctx):
        return self._next("hypothesize", ctx, HypothesisUpdate())

    async def plan(self, ctx):
        return self._next("plan", ctx, Plan(enough_evidence=True))

    async def assess(self, ctx):
        return self._next("assess", ctx, Assessment())

    async def report(self, ctx, confidence, posterior, top_id):
        return self._next("report", ctx, ReportDraft(title="scripted", root_cause="scripted", causal_chain=[]))


def make_reasoner(kind: str, model: str | None = None) -> Reasoner:
    if kind == "rules":
        return RuleReasoner()
    return LLMReasoner(model or "anthropic:claude-sonnet-5-5")
