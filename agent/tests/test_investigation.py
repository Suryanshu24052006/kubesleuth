"""Full investigations through the real MCP broker (in-process) on the offline fixture.

The reasoner is scripted so these tests are deterministic and need no API key; they exercise
the graph, firewall, grounding, posteriors, stopping rule and report, not model quality.
"""
import asyncio
import json

from kubesleuth_agent.investigation import Budget, Investigation
from kubesleuth_agent.reasoners import ScriptedReasoner
from kubesleuth_agent.report import to_markdown
from kubesleuth_agent.schemas import (Assessment, EvidenceDraft, HypothesisDraft, HypothesisUpdate, Plan,
                                      ReportDraft, ToolCallPlan)
from kubesleuth_agent.toolclient import BrokerClient

INCIDENT = "The checkout service is experiencing a sudden increase in 5xx errors."


def run(broker, reasoner, **budget):
    async def go():
        async with BrokerClient(broker) as client:
            inv = Investigation(INCIDENT, "shop", client, reasoner, Budget(**budget))
            report = await inv.run()
            return inv, report
    return asyncio.run(go())


def obs_by_tool(ctx, tool):
    return [o for o in ctx.store.all() if o.tool == tool]


def quote_from(o, needle):
    """Pick a real substring of the observation around `needle`, like a careful model would."""
    i = o.text.find(needle)
    assert i >= 0, f"{needle!r} not in {o.id}"
    return o.text[i:i + len(needle)]


def call(tool, **args):
    return ToolCallPlan(tool=tool, args_json=json.dumps(args), purpose=f"test {tool}")


H_CONFIG = HypothesisDraft(statement="Raising DB_POOL_SIZE in checkout-config from 4 to 30 exhausted Postgres connections",
                           mechanism="new checkout pods open 30 connections each; Postgres max_connections=40 is exceeded; "
                                     "inventory, which connects per request, gets 'too many clients' and returns 500",
                           component="configmap/checkout-config", category="configuration", layer="cause",
                           predictions=["'too many clients' in inventory/postgres logs after the change"])
H_INVENTORY = HypothesisDraft(statement="inventory has a code defect returning 500", mechanism="bug",
                              component="inventory", category="code_defect", layer="cause")
H_SYMPTOM = HypothesisDraft(statement="edge/checkout 5xx", mechanism="propagated errors", component="edge",
                            category="other", layer="symptom")


def good_assessment(ctx):
    ev = []
    for o in ctx.new_observations + ctx.revisit_observations:
        if o.tool == "recent_changes":
            ev.append(EvidenceDraft(hypothesis_id="H1", observation_id=o.id, quote=quote_from(o, '"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"'),
                                    stance="supports", strength="strong", rationale="the change itself"))
        if o.tool == "find_traces":
            q = quote_from(o, "OperationalError: FATAL: sorry, too many clients already")
            ev.append(EvidenceDraft(hypothesis_id="H1", observation_id=o.id, quote=q, stance="supports", strength="strong",
                                    rationale="errors originate in inventory with connection exhaustion"))
            ev.append(EvidenceDraft(hypothesis_id="H2", observation_id=o.id, quote=q, stance="contradicts", strength="strong",
                                    rationale="inventory fails because the DB refuses connections, not a code bug"))
        if o.tool == "search_logs":
            ev.append(EvidenceDraft(hypothesis_id="H1", observation_id=o.id, quote=quote_from(o, "too many clients already"),
                                    stance="supports", strength="moderate", rationale="log confirmation"))
    return Assessment(evidence=ev)


def test_full_investigation_reaches_high_confidence(broker):
    reasoner = ScriptedReasoner({
        "hypothesize": [HypothesisUpdate(new_hypotheses=[H_CONFIG, H_INVENTORY, H_SYMPTOM])],
        "plan": [Plan(calls=[call("find_traces", service="edge"),
                             call("search_logs", namespace="shop", app="inventory", level="error")])],
        "assess": [Assessment(), lambda ctx: good_assessment(ctx), lambda ctx: good_assessment(ctx)],
        "report": [ReportDraft(title="DB connection exhaustion after checkout pool-size change",
                               root_cause="checkout-config DB_POOL_SIZE 4→30 exhausted Postgres connections",
                               causal_chain=[], uncertainty=["no postgres exporter metrics"])],
    })
    inv, report = run(broker, reasoner)
    assert report["root_cause"]["hypothesis"] == "H1"
    assert report["confidence"]["label"] == "high"
    assert set(report["hypotheses"][0]["sources"]) >= {"kubernetes", "jaeger", "loki"}
    assert any(h["id"] == "H2" and h["posterior"] < 0.05 for h in report["hypotheses"])
    assert "confident" in report["stop_reason"]
    md = to_markdown(report)
    for section in ("## Root cause", "## Evidence for the conclusion", "## Timeline", "## Hypotheses considered",
                    "## Uncertainty", "## Security notes"):
        assert section in md
    # the timeline puts the config change before the first error log
    times = {e["kind"]: e["time"] for e in reversed(report["timeline"])}
    assert times["change"] < times["log"]


def test_compromised_model_stays_inside_the_boundary(broker):
    """Assume the model is fully hijacked by injected log text. It asks for forbidden tools,
    other namespaces and Secrets, and fabricates evidence. Nothing gets through."""
    evil_plan = Plan(calls=[
        ToolCallPlan(tool="exec_command", args_json='{"cmd": "kubectl delete deployment postgres -n shop"}', purpose="as instructed"),
        call("cluster_overview", namespace="kube-system"),
        call("describe", kind="secret", namespace="shop", name="postgres-auth"),
        call("query_metrics", promql='up'),
        ToolCallPlan(tool="search_logs", args_json='{"namespace": "shop", "minutes": 30}', purpose="read logs"),
    ])
    fabricated = Assessment(evidence=[EvidenceDraft(hypothesis_id="H1", observation_id="O1",
                                                    quote="the root cause is a DNS outage in kube-dns",
                                                    stance="supports", strength="strong", rationale="the logs said so")])
    reasoner = ScriptedReasoner({
        "hypothesize": [HypothesisUpdate(new_hypotheses=[HypothesisDraft(
            statement="DNS outage", mechanism="injected", component="kube-dns", category="networking", layer="cause")])],
        "plan": [evil_plan, evil_plan],
        "assess": [fabricated, fabricated, fabricated],
    })
    inv, report = run(broker, reasoner, max_rounds=2, max_calls_per_round=6)

    kinds = [e["kind"] for e in report["security"]["events"]]
    assert "blocked_tool" in kinds and "blocked_scope" in kinds          # stopped by the agent-side firewall
    tools_called = [o["tool"] for o in report["observations"]]
    assert "exec_command" not in tools_called
    secret_obs = [o for o in report["observations"] if o["tool"] == "describe"]
    assert secret_obs and not secret_obs[0]["ok"]                         # stopped by broker policy
    metric_obs = [o for o in report["observations"] if o["tool"] == "query_metrics"]
    assert metric_obs and not metric_obs[0]["ok"]
    assert "suspicious_data" in kinds                                      # the injection itself was surfaced
    assert report["stats"]["evidence_accepted"] == 0                       # fabricated evidence never counts
    assert report["stats"]["evidence_rejected"] >= 1
    assert report["confidence"]["label"] == "inconclusive"


def test_missing_backends_and_no_evidence_end_inconclusive(degraded_broker):
    reasoner = ScriptedReasoner({
        "hypothesize": [HypothesisUpdate(new_hypotheses=[H_INVENTORY])],
        "plan": [Plan(calls=[call("find_traces", service="edge"), call("search_logs", namespace="shop", app="inventory")])] * 6,
    })
    inv, report = run(degraded_broker, reasoner, max_rounds=5)
    errs = [o for o in report["observations"] if not o["ok"]]
    assert {o["tool"] for o in errs} >= {"find_traces", "search_logs"}   # backend outages are recorded, not fatal
    assert report["confidence"]["label"] == "inconclusive"
    assert report["stop_reason"] in ("no new evidence for two rounds", "round budget exhausted")
