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


class PortForward:
    """kubectl port-forward that checks itself before every use and restarts when it has died.
    Its stderr goes to a log file so a broken tunnel is visible in the run output."""

    def __init__(self, ns: str, svc: str, local: int, remote: int, health: str, logdir: Path):
        self.ns, self.svc, self.local, self.remote, self.health = ns, svc, local, remote, health
        self.log = logdir / f"port-forward-{svc}.log"
        self.proc: subprocess.Popen | None = None
        self.url = f"http://127.0.0.1:{local}"

    def _healthy(self) -> bool:
        try:
            httpx.get(self.url + self.health, timeout=3)
            return True
        except httpx.HTTPError:
            return False

    def ensure(self) -> str:
        if self.proc and self.proc.poll() is None and self._healthy():
            return self.url
        for attempt in range(1, 4):
            self.close()
            with open(self.log, "a") as fh:
                fh.write(f"--- {time.strftime('%H:%M:%S')} starting (attempt {attempt})\n")
            fh = open(self.log, "a")
            self.proc = subprocess.Popen(["kubectl", "-n", self.ns, "port-forward", f"svc/{self.svc}",
                                          f"{self.local}:{self.remote}"], stdout=fh, stderr=fh,
                                         stdin=subprocess.DEVNULL, start_new_session=True)
            for _ in range(30):
                if self.proc.poll() is not None:
                    break
                if self._healthy():
                    return self.url
                time.sleep(1)
            print(f"  port-forward to {self.svc} not ready (attempt {attempt}); see {self.log.name}", flush=True)
        raise RuntimeError(f"cannot reach {self.ns}/{self.svc} through port-forward")

    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None


def sh(*args: str):
    print("  $", " ".join(args), flush=True)
    subprocess.run(args, check=True, cwd=ROOT)


def wait_for_alert(am: PortForward, timeout: int, minimum: int = 60) -> str | None:
    start, last_err = time.time(), None
    while time.time() - start < timeout:
        try:
            alerts = httpx.get(f"{am.ensure()}/api/v2/alerts", params={"active": "true"}, timeout=5).json()
            firing = [a["labels"]["alertname"] for a in alerts if a["labels"].get("namespace") == "shop"]
            if firing and time.time() - start >= minimum:
                return ", ".join(sorted(set(firing)))
        except Exception as exc:  # keep polling; report the reason once
            if str(exc) != last_err:
                last_err = str(exc)
                print(f"  (alert poll failed: {type(exc).__name__}: {exc})", flush=True)
        time.sleep(10)
    return None


def _unwrap(exc: BaseException) -> BaseException:
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return exc


def run_one(sc: dict, args, broker: PortForward, am: PortForward, outdir: Path) -> list[dict]:
    print(f"\n=== {sc['id']}: {sc['title']}", flush=True)
    if not args.no_reset:
        sh("scenarios/run.sh", "reset")
        print(f"  settling {args.settle}s", flush=True)
        time.sleep(args.settle)
    sh("scenarios/run.sh", sc["id"], "inject")
    fired = wait_for_alert(am, int(sc.get("wait_seconds", 180)) + 120, minimum=int(sc.get("wait_seconds", 180)) // 2)
    print(f"  alert: {fired or 'none fired (investigating anyway)'}", flush=True)
    rows = []
    # Every reasoner investigates the SAME live incident, so the comparison is fair.
    for kind in args.reasoners:
        try:
            reasoner = make_reasoner(kind, args.model)
            report = asyncio.run(run_investigation(sc["incident"], "shop", f"{broker.ensure()}/mcp", reasoner,
                                                   Budget(max_rounds=args.max_rounds), quiet=False))
        except Exception as exc:  # one failing reasoner must not lose the others' results
            import traceback
            traceback.print_exc()
            exc = _unwrap(exc)
            print(f"  !! {kind} investigation failed: {type(exc).__name__}: {exc}", flush=True)
            rows.append({"scenario": sc["id"], "reasoner": kind, "alert": fired, "verdict": "error",
                         "confidence": None, "posterior": None, "evidence_sources": [], "rounds": None,
                         "tool_calls": None, "evidence_rejected": None, "duration_s": None, "tokens": 0,
                         "root_cause": f"{type(exc).__name__}: {str(exc)[:200]}"})
            continue
        name = reasoner.name.replace(":", "-").replace("/", "-")
        (outdir / f"{sc['id']}.{name}.json").write_text(json.dumps(report, indent=2, default=str))
        (outdir / f"{sc['id']}.{name}.md").write_text(to_markdown(report))
        row = {"scenario": sc["id"], "reasoner": reasoner.name, "alert": fired, **score(report, sc["ground_truth"]),
               "root_cause": report["root_cause"]["statement"], "report": f"{sc['id']}.{name}.md"}
        print(f"  -> [{reasoner.name}] {row['verdict'].upper()} ({row['confidence']}): {row['root_cause']}", flush=True)
        rows.append(row)
    return rows


def summary_md(results: list[dict], meta: dict) -> str:
    lines = [f"# kubesleuth evaluation, {meta['when']}", "", meta.get("env", ""), ""]
    for r_name in dict.fromkeys(r["reasoner"] for r in results):
        rs = [r for r in results if r["reasoner"] == r_name]
        n = len(rs)
        lines.append(f"**{r_name}**: correct {sum(r['verdict'] == 'correct' for r in rs)}/{n}, "
                     f"partial {sum(r['verdict'] == 'partial' for r in rs)}, "
                     f"inconclusive {sum(r['verdict'] == 'inconclusive' for r in rs)}, "
                     f"wrong {sum(r['verdict'] == 'wrong' for r in rs)}"
                     + (f", errors {sum(r['verdict'] == 'error' for r in rs)}" if any(r['verdict'] == 'error' for r in rs) else "")
                     + "  ")
    lines += ["", "| Scenario | Reasoner | Alert fired | Verdict | Confidence | Evidence sources | Rounds | Tool calls | "
                  "Rejected claims | Time (s) | Tokens | Root cause given by the agent |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        rc = str(r["root_cause"]).replace("|", "/").replace("\n", " ")[:160]
        link = f"[{r['scenario']}]({r['report']})" if r.get("report") else r["scenario"]
        lines.append(f"| {link} | {r['reasoner']} | {r.get('alert') or 'no'} | **{r['verdict']}** | {r['confidence']} "
                     f"({r['posterior']}) | {', '.join(r['evidence_sources'])} | {r['rounds']} | {r['tool_calls']} | "
                     f"{r['evidence_rejected']} | {r['duration_s']} | {r['tokens']} | {rc} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--scenario", action="append", help="scenario id (repeatable); default all")
    ap.add_argument("--reasoner", default="llm",
                    help="comma-separated: llm, rules or both (e.g. 'rules,llm'); all investigate the same incident")
    ap.add_argument("--model", default=os.environ.get("KUBESLEUTH_MODEL", "anthropic:claude-sonnet-5-5"))
    ap.add_argument("--max-rounds", type=int, default=6)
    ap.add_argument("--settle", type=int, default=180, help="seconds to wait after reset")
    ap.add_argument("--no-reset", action="store_true")
    ap.add_argument("--offline", action="store_true", help="score the offline fixture instead of the cluster")
    ap.add_argument("--out", help="output directory (default eval/results/<timestamp>)")
    args = ap.parse_args()
    args.reasoners = [r.strip() for r in args.reasoner.split(",") if r.strip() in ("llm", "rules")]
    if not args.reasoners:
        ap.error("--reasoner must name llm and/or rules")

    when = time.strftime("%Y%m%d-%H%M%S")
    outdir = Path(args.out) if args.out else ROOT / "eval" / "results" / f"{when}-{'-'.join(args.reasoners)}"
    outdir.mkdir(parents=True, exist_ok=True)
    scenarios = {p.parent.name: yaml.safe_load(p.read_text()) for p in sorted((ROOT / "scenarios").glob("*/scenario.yaml"))}

    results = []
    if args.offline:
        os.environ["BROKER_FIXTURE"] = str(ROOT / "fixtures" / "github-conn-saturation.json")
        from kubesleuth_broker.server import build_toolbox, create_server
        sc = scenarios["github-conn-saturation"]
        for kind in args.reasoners:
            reasoner = make_reasoner(kind, args.model)
            report = asyncio.run(run_investigation(sc["incident"], "shop", create_server(build_toolbox(), 1000, 1000),
                                                   reasoner, Budget(max_rounds=args.max_rounds), quiet=True))
            (outdir / f"offline.{kind}.md").write_text(to_markdown(report))
            results.append({"scenario": "github-conn-saturation (offline fixture)", "reasoner": reasoner.name,
                            **score(report, sc["ground_truth"]), "root_cause": report["root_cause"]["statement"],
                            "report": f"offline.{kind}.md"})
    else:
        ids = args.scenario or list(scenarios)
        broker = PortForward("kubesleuth", "kubesleuth-broker", 18090, 8090, "/healthz", outdir)
        am = PortForward("monitoring", "kps-alertmanager", 19093, 9093, "/-/healthy", outdir)
        try:
            broker.ensure()
            am.ensure()
            for sid in ids:
                results.extend(run_one(scenarios[sid], args, broker, am, outdir))
                # write partial results as we go, so a later failure never loses earlier work
                (outdir / "summary.json").write_text(json.dumps(results, indent=2))
            if not args.no_reset:
                sh("scenarios/run.sh", "reset")
        finally:
            broker.close()
            am.close()

    env = os.environ.get("EVAL_ENV_NOTE", "")
    md = summary_md(results, {"when": when, "env": env})
    (outdir / "summary.md").write_text(md)
    (outdir / "summary.json").write_text(json.dumps(results, indent=2))
    print("\n" + md + f"\nresults: {outdir}")


if __name__ == "__main__":
    main()
