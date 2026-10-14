"""Build the showcase site from the real live-evaluation results.

    python site/build.py            # writes _site/ (index.html, data.json, reports/...)

Everything shown on the site comes from results/live/*: the investigation replays are rebuilt from
each report's recorded evidence using the ledger's own weights, so the probabilities on screen are
the ones the agent computed.
"""
from __future__ import annotations

import json
import math
import re
import shutil
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = ROOT / "_site"
REPO = "https://github.com/Suryanshu24052006/kubesleuth"
UNEXPLAINED = 1.0  # same constant as agent/kubesleuth_agent/ledger.py

RUNS = [  # folder, label, date
    ("2026-10-13-run1", "Run 1", "13 Oct 2026"),
    ("2026-10-13-run2", "Run 2", "13 Oct 2026"),
    ("2026-10-14-run3", "Run 3", "14 Oct 2026"),
]
ORDER = ["knight-2012-stale-version-flag", "aws-s3-2017-capacity-removal", "aws-ebs-2012-latent-leak",
         "chef-2014-healthcheck-timeouts", "cloudflare-2019-waf-regex", "github-conn-saturation"]
FEATURED = ("2026-10-13-run2", "cloudflare-2019-waf-regex", "llm")
SHORT = {"knight-2012-stale-version-flag": "Knight Capital 2012", "aws-s3-2017-capacity-removal": "AWS S3 2017",
         "aws-ebs-2012-latent-leak": "AWS EBS 2012", "chef-2014-healthcheck-timeouts": "Chef 2014",
         "cloudflare-2019-waf-regex": "Cloudflare 2019", "github-conn-saturation": "GitHub 2022"}


def softmax(scores: dict[str, float]) -> dict[str, float]:
    s = dict(scores, unexplained=UNEXPLAINED)
    m = max(s.values())
    e = {k: math.exp(v - m) for k, v in s.items()}
    z = sum(e.values())
    return {k: round(v / z, 4) for k, v in e.items()}


def short(text: str, n: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def replay(report: dict) -> list[dict]:
    """Per-round state: tool calls, evidence accepted, and the posteriors after that round."""
    obs_round = {o["id"]: o["round"] for o in report["observations"]}
    obs_tool = {o["id"]: o for o in report["observations"]}
    hyp_ids = {h["id"] for h in report["hypotheses"]}
    born: dict[str, int] = {}
    for rd in report["rounds"]:
        for hid in rd.get("hypotheses_added", []):
            born.setdefault(hid, rd["round"])
    # opening state: the alert has fired and nothing is known yet
    steps = [{"round": -1, "label": "Alert", "calls": [], "evidence": [],
              "posteriors": {"unexplained": 1.0}, "decision": ""}]
    score = {}
    rounds = sorted({rd["round"] for rd in report["rounds"]})
    for r in rounds:
        rd = next(x for x in report["rounds"] if x["round"] == r)
        ev = [e for e in report["evidence"] if obs_round.get(e["observation"], 0) == r and e["hypothesis"] in hyp_ids]
        for e in ev:
            score[e["hypothesis"]] = score.get(e["hypothesis"], 0.0) + e["weight"]
        alive = {h: score.get(h, 0.0) for h in hyp_ids if born.get(h, 0) <= r}
        steps.append({
            "round": r,
            "label": "Triage" if r == 0 else f"Round {r}",
            "calls": [{"tool": c["tool"], "args": {k: v for k, v in (c.get("args") or {}).items() if k != "namespace"}
                       if isinstance(c.get("args"), dict) else {}, "purpose": short(c.get("purpose", ""), 110),
                       "blocked": c.get("blocked")} for c in rd.get("calls", [])],
            "evidence": [{"hyp": e["hypothesis"], "stance": e["stance"], "strength": e["strength"],
                          "source": e["source"], "quote": short(e["quote"], 160),
                          "why": short(e["rationale"], 160), "tool": obs_tool.get(e["observation"], {}).get("tool")}
                         for e in ev],
            "posteriors": softmax(alive),
            "decision": rd.get("decision") or "",
        })
    return steps


def plain_check(raw: str) -> str:
    """Security-demo output line -> a sentence a non-specialist can read."""
    m = re.match(r"(\S+) (\S+)\s*(?:in (\S+))?\s*-> (yes|no)", raw)
    if m:
        verb, res, ns, ans = m.groups()
        res = res.replace(".apps", "")
        where = f" in {ns}" if ns else " (cluster-wide)"
        return f"Broker {'can' if ans == 'yes' else 'cannot'} {verb} {res}{where}"
    m = re.match(r"(https?://\S+) -> (ok|blocked)", raw)
    if m:
        url, res = m.groups()
        return (f"Agent can reach the broker ({url})" if res == "ok"
                else f"Agent cannot reach {url}")
    if raw.startswith("no service-account token mounted"):
        return "No Kubernetes credentials mounted in the agent pod"
    return raw[0].upper() + raw[1:]


def render_report(md_text: str, title: str) -> str:
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "md_in_html"])
    return (REPORT_SHELL.replace("{{TITLE}}", title).replace("{{BODY}}", body))


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "reports").mkdir(parents=True)
    scen = {}
    for p in sorted((ROOT / "scenarios").glob("*/scenario.yaml")):
        d = yaml.safe_load(p.read_text())
        pm = d.get("postmortem", {})
        scen[d["id"]] = {"id": d["id"], "short": SHORT.get(d["id"], d["id"]), "title": d["title"], "company": pm.get("company", ""),
                         "date": str(pm.get("date", "")), "url": pm.get("url", ""),
                         "why_hard": " ".join(str(d.get("why_hard", "")).split()),
                         "incident": d.get("incident", "")}

    investigations, matrix = [], {}
    for folder, label, date in RUNS:
        run_dir = ROOT / "results" / "live" / folder
        (OUT / "reports" / folder).mkdir(parents=True, exist_ok=True)
        for row in json.loads((run_dir / "summary.json").read_text()):
            kind = "llm" if row["reasoner"].startswith("llm") else "rules"
            matrix.setdefault(row["scenario"], {}).setdefault(folder, {})[kind] = row["verdict"]
            if not row.get("report"):
                continue
            md_path = run_dir / row["report"]
            report = json.loads(md_path.with_suffix(".json").read_text())
            html_name = row["report"].replace(".md", ".html")
            title = f"{label}: {scen[row['scenario']]['company']}, {'LLM agent' if kind == 'llm' else 'baseline'}"
            (OUT / "reports" / folder / html_name).write_text(render_report(md_path.read_text(), title))
            usage = (report.get("stats") or {}).get("llm_usage") or {}
            investigations.append({
                "key": f"{folder}/{row['scenario']}/{kind}", "run": folder, "run_label": label, "date": date,
                "scenario": row["scenario"], "reasoner": kind, "verdict": row["verdict"],
                "incident": report["incident"], "root_cause": report["root_cause"]["statement"],
                "confidence": report["confidence"]["label"], "posterior": report["confidence"]["posterior"],
                "models": [m.split(":")[-1] for m in usage.get("models", [])],
                "hypotheses": [{"id": h["id"], "statement": short(h["statement"], 150), "layer": h["layer"],
                                "component": h["component"]} for h in report["hypotheses"]],
                "steps": replay(report), "report": f"reports/{folder}/{html_name}",
                "stats": report.get("stats", {}),
            })

    sec_path = ROOT / "results" / "live" / RUNS[-1][0] / "security-demo.txt"
    security = []
    for line in sec_path.read_text().splitlines():
        m = re.match(r"\s*PASS (.+)", line)
        if m:
            security.append({"check": plain_check(m.group(1).strip()), "ok": True})
        m = re.match(r"(.+?)\s{2,}(\S+)\s+BLOCKED ✓", line)
        if m:
            security.append({"check": f"Attack refused: {m.group(1).strip()}", "ok": True})

    data = {"repo": REPO, "featured": "/".join(FEATURED), "runs": [{"id": f, "label": l, "date": d} for f, l, d in RUNS],
            "order": ORDER, "scenarios": scen, "matrix": matrix, "investigations": investigations,
            "security": security}
    (OUT / "data.json").write_text(json.dumps(data, separators=(",", ":")))
    shutil.copy(SITE / "index.html", OUT / "index.html")
    (OUT / ".nojekyll").write_text("")
    print(f"built {len(investigations)} investigations, {len(security)} security checks -> {OUT}")


REPORT_SHELL = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{{TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<style>
:root{--paper:#F3F4EF;--ink:#16233B;--muted:#68707C;--line:#D9DCD3;--blue:#2C5FD9}
@media (prefers-color-scheme:dark){:root{--paper:#121A29;--ink:#E7EAF0;--muted:#9AA3B2;--line:#2A3448;--blue:#7FA2F5}}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 "Source Serif 4",Georgia,serif}
main{max-width:980px;margin:0 auto;padding:32px 20px 80px}
a{color:var(--blue)}h1,h2,h3{font-family:"Familjen Grotesk",system-ui,sans-serif;line-height:1.2}
h1{font-size:1.9rem}h2{font-size:1.3rem;margin-top:2.2em}
table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;font-size:.88rem;margin:1em 0}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
code{font:13px/1.5 "JetBrains Mono",monospace;background:rgba(127,127,127,.12);padding:1px 4px;border-radius:3px;word-break:break-word}
details{margin:1em 0}summary{cursor:pointer;font-family:"Familjen Grotesk",sans-serif}
.back{font-family:"Familjen Grotesk",sans-serif;font-size:.95rem}
</style></head><body><main><p class="back"><a href="../../index.html#replay">Back to kubesleuth</a></p>
{{BODY}}</main></body></html>"""

if __name__ == "__main__":
    main()
