"""Regression: live clusters return far larger results than the recorded fixture.

The first run on a real kind cluster crashed in timeline building because trimmed lists
contained a "...N more omitted" marker string. This test inflates the fixture until every
list-heavy tool result is trimmed, then runs a full investigation and report.
"""
import asyncio
import json

from conftest import FIXTURE, make_broker
from kubesleuth_agent.investigation import Budget, Investigation
from kubesleuth_agent.reasoners import RuleReasoner
from kubesleuth_agent.report import to_markdown
from kubesleuth_agent.toolclient import BrokerClient


def inflated_fixture(tmp_path):
    doc = json.loads(FIXTURE.read_text())
    for i in range(250):  # noisy change history, like the HPA and rollouts on a busy cluster
        doc["journal"].append({
            "time": f"@-{1800 + i * 5}", "observed_at": f"@-{1800 + i * 5}", "kind": "hpa", "namespace": "shop",
            "name": f"noise-{i}", "change": "modified",
            "fields": [{"field": "spec.maxReplicas", "old": i, "new": i + 1}] * 3,
            "actor": {"manager": "kube-controller-manager"}, "source": "change-journal"})
    base = doc["kube"]["event"][0]
    for i in range(400):
        e = json.loads(json.dumps(base))
        e["metadata"]["name"] = f"noise.{i}"
        e["involvedObject"]["name"] = f"pod-noise-{i}"
        e["message"] = f"Readiness probe failed for replica number {i} " + "x" * 200
        doc["kube"]["event"].append(e)
    path = tmp_path / "big.json"
    path.write_text(json.dumps(doc))
    return path


def test_trimmed_lists_keep_their_element_types(tmp_path):
    from kubesleuth_broker.tools import fit
    data = {"changes": [{"time": str(i), "fields": [{"field": "x"}] * 50} for i in range(500)]}
    out, cap = fit(data, budget=4000)
    assert cap and all(isinstance(c, dict) for c in out["changes"])
    assert all(isinstance(f, dict) for c in out["changes"] for f in c["fields"])


def test_full_investigation_on_inflated_results(tmp_path):
    broker = make_broker(inflated_fixture(tmp_path))

    async def go():
        async with BrokerClient(broker) as client:
            inv = Investigation("checkout 5xx", "shop", client, RuleReasoner(), Budget(max_rounds=4))
            return inv, await inv.run()
    inv, report = asyncio.run(go())
    rc = next(o for o in inv.store.all() if o.tool == "recent_changes")
    assert rc.envelope["truncated"] is True
    # newest changes survive trimming: the DB_POOL_SIZE change (9 min ago) is kept, old noise is cut
    fields = [f["field"] for c in rc.envelope["data"]["changes"] for f in c["fields"]]
    assert "data.DB_POOL_SIZE" in fields
    assert report["root_cause"]["hypothesis"]
    assert "## Timeline" in to_markdown(report)
