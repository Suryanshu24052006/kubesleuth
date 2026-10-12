"""In-cluster agent service.

  POST /alerts          Alertmanager webhook -> starts an investigation per alert group (deduplicated)
  POST /investigate     {"incident": "...", "namespace": "shop"} -> {"id": ...}
  GET  /investigations  list;  GET /investigations/{id} (json)  /investigations/{id}.md (markdown)
  GET  /                tiny HTML index of reports

The pod that runs this has NO Kubernetes credentials (automountServiceAccountToken: false)
and its NetworkPolicy only lets it reach the broker, DNS and the LLM API.
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
import time
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from .cli import run_investigation
from .investigation import Budget
from .reasoners import make_reasoner
from .report import to_markdown

log = logging.getLogger("kubesleuth.server")
REPORT_DIR = Path(os.environ.get("REPORT_DIR", "/data/reports"))
BROKER_URL = os.environ.get("BROKER_URL", "http://kubesleuth-broker:8090/mcp")
NAMESPACE = os.environ.get("KUBESLEUTH_NAMESPACE", "shop")
COOLDOWN_S = int(os.environ.get("ALERT_COOLDOWN_SECONDS", "900"))
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT_INVESTIGATIONS", "1"))

app = FastAPI(title="kubesleuth agent")
_status: dict[str, dict] = {}
_recent_groups: dict[str, float] = {}
_sem = asyncio.Semaphore(MAX_CONCURRENT)
_SAFE_ID = re.compile(r"^[0-9]{8}-[0-9]{6}-[0-9a-f]{6}$")


async def _investigate(incident: str, namespace: str, key: str):
    _status[key] = {"state": "queued", "incident": incident, "since": time.time()}
    async with _sem:
        _status[key]["state"] = "running"
        try:
            reasoner = make_reasoner(os.environ.get("KUBESLEUTH_REASONER", "llm"), os.environ.get("KUBESLEUTH_MODEL"))
            report = await run_investigation(incident, namespace, BROKER_URL, reasoner,
                                             Budget(max_rounds=int(os.environ.get("MAX_ROUNDS", "6"))), quiet=True)
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
            (REPORT_DIR / f"{report['id']}.json").write_text(json.dumps(report, indent=2, default=str))
            (REPORT_DIR / f"{report['id']}.md").write_text(to_markdown(report))
            _status[key].update(state="done", report_id=report["id"],
                                root_cause=report["root_cause"]["statement"], confidence=report["confidence"]["label"])
            log.info("investigation %s done: %s", report["id"], report["root_cause"]["statement"])
        except Exception as exc:
            log.exception("investigation failed")
            _status[key].update(state="failed", error=f"{type(exc).__name__}: {str(exc)[:300]}")


def _incident_from_alert(a: dict) -> str:
    """Alert text is templated from rule annotations, but label values can carry workload-controlled
    strings, so keep it short and let the agent treat everything else as data."""
    labels, ann = a.get("labels", {}), a.get("annotations", {})
    parts = [f"Alert {labels.get('alertname', '?')} ({labels.get('severity', '?')}) is firing"]
    if labels.get("service"):
        parts.append(f"for service {labels['service']}")
    if ann.get("summary"):
        parts.append(f"- {ann['summary'][:200]}")
    parts.append(f"since {a.get('startsAt', '?')}.")
    return " ".join(parts)


@app.post("/alerts")
async def alerts(request: Request, background: BackgroundTasks):
    body = await request.json()
    group = body.get("groupKey") or json.dumps(body.get("groupLabels", {}), sort_keys=True)
    firing = [a for a in body.get("alerts", []) if a.get("status") == "firing"]
    if not firing:
        return {"accepted": False, "reason": "no firing alerts"}
    now = time.time()
    if now - _recent_groups.get(group, 0) < COOLDOWN_S:
        return {"accepted": False, "reason": "alert group already investigated recently"}
    _recent_groups[group] = now
    ns = (firing[0].get("labels") or {}).get("namespace", NAMESPACE)
    if ns != NAMESPACE:
        return {"accepted": False, "reason": f"namespace {ns} outside scope"}
    incident = " ".join(_incident_from_alert(a) for a in firing[:3])
    key = f"alert-{int(now)}"
    background.add_task(_investigate, incident, ns, key)
    return {"accepted": True, "key": key, "incident": incident}


@app.post("/investigate")
async def investigate(payload: dict, background: BackgroundTasks):
    incident = str(payload.get("incident", ""))[:500]
    if not incident:
        raise HTTPException(400, "incident is required")
    ns = payload.get("namespace", NAMESPACE)
    if ns != NAMESPACE:
        raise HTTPException(403, "namespace outside scope")
    key = f"manual-{int(time.time() * 1000)}"
    background.add_task(_investigate, incident, ns, key)
    return {"key": key}


@app.get("/investigations")
def investigations():
    return _status


@app.get("/investigations/{rid}")
def get_report(rid: str):
    md = rid.endswith(".md")
    rid = rid.removesuffix(".md")
    if not _SAFE_ID.match(rid):
        raise HTTPException(400, "bad id")
    path = REPORT_DIR / f"{rid}.{'md' if md else 'json'}"
    if not path.exists():
        raise HTTPException(404, "not found")
    return PlainTextResponse(path.read_text()) if md else json.loads(path.read_text())


@app.get("/", response_class=HTMLResponse)
def index():
    rows = []
    for p in sorted(REPORT_DIR.glob("*.json"), reverse=True)[:50] if REPORT_DIR.exists() else []:
        r = json.loads(p.read_text())
        rows.append(f"<tr><td>{html.escape(r['started_at'])}</td><td>{html.escape(r['incident'][:90])}</td>"
                    f"<td>{html.escape(r['confidence']['label'])}</td><td>{html.escape(str(r['root_cause']['statement'])[:160])}</td>"
                    f"<td><a href='/investigations/{r['id']}.md'>md</a> · <a href='/investigations/{r['id']}'>json</a></td></tr>")
    running = "".join(f"<li>{html.escape(k)}: {html.escape(v['state'])} — {html.escape(v['incident'][:100])}</li>"
                      for k, v in _status.items() if v["state"] in ("queued", "running"))
    return ("<html><head><title>kubesleuth</title><style>body{font-family:system-ui;margin:2rem}td{padding:4px 8px;"
            "border-bottom:1px solid #ddd;vertical-align:top}</style></head><body><h1>kubesleuth reports</h1>"
            f"<ul>{running}</ul><table><tr><th>Started</th><th>Incident</th><th>Confidence</th><th>Root cause</th><th></th></tr>"
            + "".join(rows) + "</table></body></html>")


@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")
