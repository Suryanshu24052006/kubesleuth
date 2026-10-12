"""kubesleuth CLI.

  # live cluster (broker port-forwarded to localhost:8090)
  python -m kubesleuth_agent investigate "checkout is returning 5xx" --broker http://localhost:8090/mcp

  # offline: in-process broker serving a recorded snapshot, no cluster needed
  python -m kubesleuth_agent investigate "edge 5xx alert" --fixture fixtures/github-conn-saturation.json --reasoner rules
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from .investigation import Budget, Investigation
from .reasoners import make_reasoner
from .report import to_markdown
from .toolclient import BrokerClient


def _printer(quiet: bool):
    def emit(kind: str, p: dict):
        if quiet:
            return
        if kind == "observation":
            args = ", ".join(f"{k}={v}" for k, v in p["args"].items() if k != "namespace")
            print(f"  {'✓' if p['ok'] else '✗'} {p['id']} {p['tool']}({args})  — {p['purpose'][:70]}", flush=True)
        elif kind == "hypothesis":
            print(f"  + {p['id']} [{p['layer']}] {p['statement'][:110]}", flush=True)
        elif kind == "blocked":
            print(f"  ⛔ blocked {p['tool']}: {p['reason'][:100]}", flush=True)
        elif kind == "round":
            bars = "  ".join(f"{k}:{v:.2f}" for k, v in sorted(p["posteriors"].items(), key=lambda kv: -kv[1])[:5])
            print(f"── round {p['round']} → {p['decision']}\n   posteriors {bars}", flush=True)
    return emit


def _broker_target(args):
    if args.fixture:
        os.environ["BROKER_FIXTURE"] = str(Path(args.fixture).resolve())
        os.environ.setdefault("ALLOWED_NAMESPACES", args.namespace)
        try:
            from kubesleuth_broker.server import build_toolbox, create_server
        except ImportError:
            sys.exit("--fixture needs the broker package on PYTHONPATH (pip install -e broker/)")
        for noisy in ("kubesleuth.audit", "mcp", "httpx"):
            logging.getLogger(noisy).setLevel(logging.WARNING)
        return create_server(build_toolbox(), rate=1000, burst=1000)
    return args.broker


async def run_investigation(incident: str, namespace: str, target, reasoner, budget: Budget, quiet: bool = False,
                            on_event=None):
    async with BrokerClient(target) as broker:
        inv = Investigation(incident, namespace, broker, reasoner, budget, on_event=on_event or _printer(quiet))
        return await inv.run()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="kubesleuth")
    sub = ap.add_subparsers(dest="cmd", required=True)
    inv = sub.add_parser("investigate", help="investigate an incident and write an RCA")
    inv.add_argument("incident", help='e.g. "The checkout service is experiencing a sudden increase in 5xx errors."')
    inv.add_argument("--namespace", "-n", default=os.environ.get("KUBESLEUTH_NAMESPACE", "shop"))
    inv.add_argument("--broker", default=os.environ.get("BROKER_URL", "http://localhost:8090/mcp"))
    inv.add_argument("--fixture", help="offline snapshot instead of a live broker")
    inv.add_argument("--reasoner", choices=["llm", "rules"], default=os.environ.get("KUBESLEUTH_REASONER", "llm"))
    inv.add_argument("--model", default=os.environ.get("KUBESLEUTH_MODEL", "anthropic:claude-sonnet-5-5"),
                     help="LangChain model id, e.g. anthropic:claude-sonnet-5-5, google_genai:gemini-2.5-flash, openai:gpt-4.1")
    inv.add_argument("--max-rounds", type=int, default=6)
    inv.add_argument("--out", default="reports")
    inv.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(name)s %(levelname)s %(message)s")

    reasoner = make_reasoner(args.reasoner, args.model)
    print(f"kubesleuth: investigating in namespace '{args.namespace}' with {reasoner.name}")
    report = asyncio.run(run_investigation(args.incident, args.namespace, _broker_target(args), reasoner,
                                           Budget(max_rounds=args.max_rounds), args.quiet))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    md = to_markdown(report)
    (out / f"{report['id']}.json").write_text(json.dumps(report, indent=2, default=str))
    (out / f"{report['id']}.md").write_text(md)
    c = report["confidence"]
    print(f"\nROOT CAUSE ({c['label']}, p={c['posterior']:.2f}): {report['root_cause']['statement']}")
    print(f"report: {out / (report['id'] + '.md')}")


if __name__ == "__main__":
    main()
