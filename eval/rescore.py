"""Re-score a saved evaluation run with the current scorer and ground truth.

    python eval/rescore.py results/live/2026-10-13-run2

Reads every <scenario>.<reasoner>.json report in the directory, recomputes the verdicts and rewrites
summary.json and summary.md. Investigations are not rerun; only the grading changes. Used when the
scorer was made stricter, so that all published runs are graded by the same rules.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "eval")]
from run_eval import summary_md  # noqa: E402
from score import score  # noqa: E402


def rescore(run_dir: Path) -> list[dict]:
    scenarios = {p.parent.name: yaml.safe_load(p.read_text()) for p in (ROOT / "scenarios").glob("*/scenario.yaml")}
    old = {(r["scenario"], r["reasoner"]): r for r in json.loads((run_dir / "summary.json").read_text())}
    rows = []
    for (sid, reasoner), prev in old.items():
        report_md = prev.get("report")
        report_json = run_dir / report_md.replace(".md", ".json") if report_md else None
        if not report_json or not report_json.exists():
            rows.append(prev)  # errors or reports that were not kept: unchanged
            continue
        report = json.loads(report_json.read_text())
        row = {k: prev[k] for k in ("scenario", "reasoner", "reasoner_detail", "alert", "report") if k in prev}
        row.update(score(report, scenarios[sid]["ground_truth"]))
        row["root_cause"] = report["root_cause"]["statement"]
        if prev.get("verdict") != row["verdict"]:
            row["previous_verdict"] = prev.get("verdict")
        rows.append(row)
    return rows


if __name__ == "__main__":
    run_dir = Path(sys.argv[1])
    rows = rescore(run_dir)
    (run_dir / "summary.json").write_text(json.dumps(rows, indent=2))
    first = (run_dir / "summary.md").read_text().splitlines()
    when = first[0].split(",")[-1].strip() if first else run_dir.name
    env = next((l for l in first[1:4] if l.strip()), "")
    (run_dir / "summary.md").write_text(summary_md(rows, {"when": when, "env": env + " Graded with eval/score.py (strict scorer)."}))
    for r in rows:
        change = f"  (was {r['previous_verdict']})" if r.get("previous_verdict") else ""
        print(f"{r['scenario']:32} {r['reasoner'][:5]:6} {r['verdict']}{change}")
