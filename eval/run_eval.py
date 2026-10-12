"""Run every scenario end to end against the live kind cluster and score the RCAs.

    python eval/run_eval.py                         # all scenarios, LLM reasoner
    python eval/run_eval.py -s github-conn-saturation -s aws-s3-2017-capacity-removal
    python eval/run_eval.py --reasoner rules        # baseline without an LLM
    python eval/run_eval.py --offline               # score the offline fixture only (no cluster)

For each scenario: reset to baseline -> settle -> inject -> wait for an alert (or the scenario's
wait time) -> investigate through the broker (port-forwarded) -> score against ground truth -> reset.
The agent never sees the scenario file; it only receives the scenario's incident text.
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "agent"), str(ROOT / "broker"), str(ROOT / "eval")]

from kubesleuth_agent.cli import run_investigation  # noqa: E402
from kubesleuth_agent.investigation import Budget  # noqa: E402
from kubesleuth_agent.reasoners import make_reasoner  # noqa: E402
from kubesleuth_agent.report import to_markdown  # noqa: E402
from score import score  # noqa: E402


@contextlib.contextmanager
def port_forward(ns: str, svc: str, local: int, remote: int):
    p = subprocess.Popen(["kubectl", "-n", ns, "port-forward", f"svc/{svc}", f"{local}:{remote}"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                httpx.get(f"http://127.0.0.1:{local}/", timeout=1)
                break
            except httpx.HTTPError:
                time.sleep(0.5)
        yield f"http://127.0.0.1:{local}"
    finally:
        p.terminate()


def sh(*args: str):
    print("  $", " ".join(args), flush=True)
    subprocess.run(args, check=True, cwd=ROOT)


def wait_for_alert(am_url: str, timeout: int, minimum: int = 60) -> str | None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            alerts = httpx.get(f"{am_url}/api/v2/alerts", params={"active": "true"}, timeout=5).json()
            firing = [a["labels"]["alertname"] for a in alerts if a["labels"].get("namespace") == "shop"]
            if firing and time.time() - start >= minimum:
                return ", ".join(sorted(set(firing)))
        except (httpx.HTTPError, ValueError, KeyError):
            pass
        time.sleep(10)
    return None


def run_one(sc: dict, args, broker_url: str, am_url: str, outdir: Path) -> dict:
    print(f"\n=== {sc['id']}: {sc['title']}")
    if not args.no_reset:
        sh("scenarios/run.sh", "reset")
        print(f"  settling {args.settle}s", flush=True)
        time.sleep(args.settle)
    sh("scenarios/run.sh", sc["id"], "inject")
    fired = wait_for_alert(am_url, int(sc.get("wait_seconds", 180)) + 120, minimum=int(sc.get("wait_seconds", 180)) // 2)
    print(f"  alert: {fired or 'none fired (investigating anyway)'}", flush=True)
    reasoner = make_reasoner(args.reasoner, args.model)
    report = asyncio.run(run_investigation(sc["incident"], "shop", f"{broker_url}/mcp", reasoner,
                                           Budget(max_rounds=args.max_rounds), quiet=False))
    result = {"scenario": sc["id"], "alert": fired, **score(report, sc["ground_truth"]),
              "root_cause": report["root_cause"]["statement"], "report_id": report["id"]}
    (outdir / f"{sc['id']}.json").write_text(json.dumps(report, indent=2, default=str))
    (outdir / f"{sc['id']}.md").write_text(to_markdown(report))
    print(f"  -> {result['verdict'].upper()} ({result['confidence']}): {result['root_cause']}", flush=True)
    return result


def summary_md(results: list[dict], meta: dict) -> str:
    n = len(results)
    correct = sum(r["verdict"] == "correct" for r in results)
    lines = [f"# kubesleuth evaluation — {meta['when']}", "",
             f"Reasoner: `{meta['reasoner']}` · scenarios: {n} · **correct {correct}/{n}**, "
             f"partial {sum(r['verdict'] == 'partial' for r in results)}, "
             f"inconclusive {sum(r['verdict'] == 'inconclusive' for r in results)}, "
             f"wrong {sum(r['verdict'] == 'wrong' for r in results)}", "",
             "| Scenario | Verdict | Confidence | Evidence sources | Rounds | Tool calls | Rejected claims | Time (s) | Tokens | Root cause (agent) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['scenario']} | **{r['verdict']}** | {r['confidence']} ({r['posterior']}) | "
                     f"{', '.join(r['evidence_sources'])} | {r['rounds']} | {r['tool_calls']} | {r['evidence_rejected']} | "
                     f"{r['duration_s']} | {r['tokens']} | {str(r['root_cause'])[:140]} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--scenario", action="append", help="scenario id (repeatable); default all")
    ap.add_argument("--reasoner", choices=["llm", "rules"], default="llm")
    ap.add_argument("--model", default=os.environ.get("KUBESLEUTH_MODEL", "anthropic:claude-sonnet-5-5"))
    ap.add_argument("--max-rounds", type=int, default=6)
    ap.add_argument("--settle", type=int, default=180, help="seconds to wait after reset")
    ap.add_argument("--no-reset", action="store_true")
    ap.add_argument("--offline", action="store_true", help="score the offline fixture instead of the cluster")
    args = ap.parse_args()

    when = time.strftime("%Y%m%d-%H%M%S")
    outdir = ROOT / "eval" / "results" / f"{when}-{args.reasoner}"
    outdir.mkdir(parents=True, exist_ok=True)
    scenarios = {p.parent.name: yaml.safe_load(p.read_text()) for p in sorted((ROOT / "scenarios").glob("*/scenario.yaml"))}

    results = []
    if args.offline:
        os.environ["BROKER_FIXTURE"] = str(ROOT / "fixtures" / "github-conn-saturation.json")
        from kubesleuth_broker.server import build_toolbox, create_server
        sc = scenarios["github-conn-saturation"]
        report = asyncio.run(run_investigation(sc["incident"], "shop", create_server(build_toolbox(), 1000, 1000),
                                               make_reasoner(args.reasoner, args.model), Budget(max_rounds=args.max_rounds)))
        (outdir / "offline.md").write_text(to_markdown(report))
        results.append({"scenario": "github-conn-saturation (offline fixture)", **score(report, sc["ground_truth"]),
                        "root_cause": report["root_cause"]["statement"]})
    else:
        ids = args.scenario or list(scenarios)
        with port_forward("kubesleuth", "kubesleuth-broker", 18090, 8090) as broker, \
                port_forward("monitoring", "kps-alertmanager", 19093, 9093) as am:
            for i, sid in enumerate(ids):
                results.append(run_one(scenarios[sid], args, broker, am, outdir))
            if not args.no_reset:
                sh("scenarios/run.sh", "reset")

    md = summary_md(results, {"when": when, "reasoner": args.reasoner if args.reasoner == "rules" else args.model})
    (outdir / "summary.md").write_text(md)
    (outdir / "summary.json").write_text(json.dumps(results, indent=2))
    print("\n" + md + f"\nresults: {outdir}")


if __name__ == "__main__":
    main()
