"""Attack the broker the way a hijacked agent would, and check every attempt is refused.

    python -m kubesleuth_agent.security_probe --broker http://localhost:8090/mcp
    python -m kubesleuth_agent.security_probe --fixture fixtures/github-conn-saturation.json   (offline)

Exit code 0 only if every attack is blocked and the one legitimate call succeeds.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from mcp import Client

ATTACKS = [
    ("read Secret object", "describe", {"kind": "secret", "namespace": "shop", "name": "postgres-auth"}, "policy_denied"),
    ("read ServiceAccount", "describe", {"kind": "serviceaccount", "namespace": "shop", "name": "default"}, "policy_denied"),
    ("escape namespace scope", "cluster_overview", {"namespace": "kube-system"}, "policy_denied"),
    ("read the agent's own namespace", "get_events", {"namespace": "kubesleuth"}, "policy_denied"),
    ("logs of a pod outside scope", "pod_logs", {"namespace": "kube-system", "pod": "kube-apiserver-kubesleuth-control-plane"}, "policy_denied"),
    ("path traversal in pod name", "pod_logs", {"namespace": "shop", "pod": "../../../etc/passwd"}, "policy_denied"),
    ("unscoped PromQL (all namespaces)", "query_metrics", {"promql": "sum(container_memory_working_set_bytes)"}, "policy_denied"),
    ("PromQL regex widening scope", "query_metrics", {"promql": 'up{namespace=~".+"}'}, "policy_denied"),
    ("PromQL negative matcher", "query_metrics", {"promql": 'kube_secret_info{namespace!="shop"}'}, "policy_denied"),
    ("LogQL injection via filter", "search_logs", {"namespace": "shop", "contains": '"} or {namespace="kube-system'}, "OK_ESCAPED"),
    ("non-existent exec tool", "exec", {"command": "cat /var/run/secrets/kubernetes.io/serviceaccount/token"}, "Unknown tool"),
    ("non-existent delete tool", "delete_deployment", {"namespace": "shop", "name": "postgres"}, "Unknown tool"),
    ("malformed arguments", "get_events", {"namespace": "shop", "minutes": "1; rm -rf /"}, "valid integer"),
    ("oversized time window (DoS)", "search_logs", {"namespace": "shop", "minutes": 999999}, "less than or equal"),
]
LEGIT = ("legitimate read inside scope", "cluster_overview", {"namespace": "shop"})


async def probe(target) -> int:
    failures = 0
    async with Client(target) as c:
        tools = (await c.list_tools()).tools
        print(f"broker advertises {len(tools)} tools, all read-only: "
              f"{all(t.annotations and t.annotations.read_only_hint for t in tools)}")
        print(f"{'attack':40} {'tool':18} result")
        for name, tool, args, expect in ATTACKS:
            r = await c.call_tool(tool, args)
            text = r.content[0].text if r.content else ""
            if expect == "OK_ESCAPED":
                # allowed, but the payload must stay inside a quoted, escaped line-filter string
                logql = json.loads(text)["data"]["logql"] if not r.is_error else ""
                ok = logql.startswith('{namespace="shop"} |= "') and '\\"} or {namespace=' in logql
            else:
                ok = r.is_error and expect in text
            failures += not ok
            print(f"{name:40} {tool:18} {'BLOCKED ✓' if ok else 'NOT BLOCKED ✗'}  {text[:90]!r}")
        name, tool, args = LEGIT
        r = await c.call_tool(tool, args)
        ok = not r.is_error
        failures += not ok
        print(f"{name:40} {tool:18} {'ALLOWED ✓' if ok else 'FAILED ✗'}")
    print(f"\nall {len(ATTACKS)} attacks blocked, legitimate access works" if failures == 0 else f"\n{failures} check(s) FAILED")
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default=os.environ.get("BROKER_URL", "http://localhost:8090/mcp"))
    ap.add_argument("--fixture")
    a = ap.parse_args()
    import logging
    logging.getLogger("mcp").setLevel(logging.CRITICAL)
    logging.getLogger("kubesleuth.audit").setLevel(logging.WARNING)
    target = a.broker
    if a.fixture:
        os.environ["BROKER_FIXTURE"] = a.fixture
        from kubesleuth_broker.server import build_toolbox, create_server
        target = create_server(build_toolbox(), 1000, 1000)
    sys.exit(asyncio.run(probe(target)))


if __name__ == "__main__":
    main()
