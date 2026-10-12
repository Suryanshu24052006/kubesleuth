"""End-to-end over the real MCP protocol (in-process transport), against the offline fixture."""
import asyncio
import json
import logging
import os
from pathlib import Path

import pytest
from mcp import Client

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "github-conn-saturation.json"


@pytest.fixture(scope="module")
def server():
    os.environ["BROKER_FIXTURE"] = str(FIXTURE)
    os.environ["ALLOWED_NAMESPACES"] = "shop"
    from kubesleuth_broker.server import build_toolbox, create_server
    return create_server(build_toolbox(), rate=1000, burst=1000)


def call(server, name, args):
    async def go():
        async with Client(server) as c:
            return await c.call_tool(name, args)
    return asyncio.run(go())


def test_tool_catalogue_is_read_only(server):
    async def go():
        async with Client(server) as c:
            return (await c.list_tools()).tools
    tools = asyncio.run(go())
    names = {t.name for t in tools}
    assert names == {"active_alerts", "cluster_overview", "get_events", "recent_changes", "describe", "pod_logs",
                     "search_logs", "workload_metrics", "query_metrics", "find_traces", "service_map"}
    for t in tools:
        assert t.annotations.read_only_hint is True and t.annotations.destructive_hint is False
    # nothing in the catalogue can mutate, exec or read secrets
    assert not any(w in n for n in names for w in ("delete", "exec", "apply", "patch", "scale", "secret", "shell"))


def test_happy_path_returns_envelope(server):
    r = call(server, "recent_changes", {"namespace": "shop", "minutes": 60})
    assert not r.is_error
    env = json.loads(r.content[0].text)
    assert env["tool"] == "recent_changes"
    fields = [f["field"] for c in env["data"]["changes"] for f in c["fields"]]
    assert "data.DB_POOL_SIZE" in fields


@pytest.mark.parametrize("name,args,expect", [
    ("cluster_overview", {"namespace": "kube-system"}, "policy_denied"),
    ("describe", {"kind": "secret", "namespace": "shop", "name": "postgres-auth"}, "policy_denied"),
    ("query_metrics", {"promql": "up"}, "policy_denied"),
    ("query_metrics", {"promql": 'container_memory_working_set_bytes{namespace="monitoring"}'}, "policy_denied"),
    ("pod_logs", {"namespace": "shop", "pod": "../../etc/passwd"}, "policy_denied"),
    ("search_logs", {"namespace": "shop", "minutes": 100000}, "less than or equal"),
    ("get_events", {"namespace": "shop", "minutes": "sixty"}, "valid integer"),
    ("delete_namespace", {"namespace": "shop"}, "Unknown tool"),
    ("kubectl", {"args": "delete deploy checkout"}, "Unknown tool"),
])
def test_out_of_boundary_calls_are_refused(server, name, args, expect):
    r = call(server, name, args)
    assert r.is_error, r
    assert expect in r.content[0].text


def test_injection_is_flagged_not_executed(server):
    r = call(server, "search_logs", {"namespace": "shop", "minutes": 30})
    env = json.loads(r.content[0].text)
    flagged = env["security"]["suspicious_instructions"]
    assert flagged and any("IGNORE ALL PREVIOUS INSTRUCTIONS" in f["excerpt"] for f in flagged)


def test_audit_log_records_denials(server, caplog):
    with caplog.at_level(logging.INFO, logger="kubesleuth.audit"):
        call(server, "cluster_overview", {"namespace": "kube-system"})
    rec = json.loads(caplog.records[-1].getMessage())
    assert rec["tool"] == "cluster_overview" and rec["outcome"] == "denied"


def test_rate_limit():
    os.environ["BROKER_FIXTURE"] = str(FIXTURE)
    from kubesleuth_broker.server import build_toolbox, create_server
    srv = create_server(build_toolbox(), rate=0.0001, burst=2)
    async def go():
        async with Client(srv) as c:
            return [await c.call_tool("active_alerts", {}) for _ in range(4)]
    res = asyncio.run(go())
    assert [r.is_error for r in res] == [False, False, True, True]
    assert "rate_limited" in res[-1].content[0].text


def test_degraded_backends_are_reported():
    os.environ["BROKER_FIXTURE"] = str(FIXTURE.with_name("github-conn-saturation-degraded.json"))
    from kubesleuth_broker.server import build_toolbox, create_server
    srv = create_server(build_toolbox(), rate=1000, burst=1000)
    r = call(srv, "find_traces", {"service": "edge"})
    assert r.is_error and "backend_unavailable" in r.content[0].text
