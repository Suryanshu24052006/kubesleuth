# kubesleuth — an AI agent for Kubernetes root-cause analysis

Inter IIT Tech Meet 15.0 · Prepathon · Development PS

kubesleuth investigates Kubernetes incidents the way an SRE does: it forms **competing hypotheses**,
gathers evidence from **Kubernetes, metrics, logs, traces and change history** through a
**read-only MCP broker**, updates beliefs with a **verifiable evidence ledger**, and stops when the
evidence is decisive or says what is missing. The environment reproduces **six real production
post-mortems** (Cloudflare 2019, Knight Capital 2012, AWS S3 2017, GitHub, Chef 2014, AWS EBS 2012) on a
local kind cluster with a ground truth for each.

```
            Alertmanager webhook / CLI / HTTP
                          │ incident
┌─────────────────────────▼──────────────────────────┐   namespace kubesleuth (PSS "restricted",
│ agent  (LangGraph)          NO k8s credentials     │   default-deny NetworkPolicy)
│  triage → hypothesize → plan → act → assess → decide ──► report (facts / hypotheses / evidence /
│            ▲   LLM         firewall   LLM   ledger │            timeline / confidence / uncertainty)
│            └──────────────── loop ─────────────────┘
└─────────────────────────┬──────────────────────────┘
                          │ MCP (streamable HTTP), 11 read-only tools
┌─────────────────────────▼──────────────────────────┐
│ broker                 read-only ServiceAccount    │  policy · redaction · injection flagging ·
│  change journal (watch) · log mining · onsets      │  rate limit · audit log
└──┬──────────────┬──────────────┬─────────────┬─────┘
 kube-apiserver  Prometheus     Loki          Jaeger      (+ Alertmanager)
 (RBAC: get/list/watch in `shop` only, no Secrets, no exec)
```

## What makes it different

| Idea | Why it matters |
|---|---|
| **Evidence ledger with machine-verified quotes** | Every evidence claim must cite an observation id and quote it *verbatim*; the code checks the substring. Fabricated or hallucinated evidence is rejected and counted, never scored. |
| **Posteriors computed by code, not by the model** | The LLM grades evidence (supports/contradicts, weak/moderate/strong); fixed log-odds weights, source-diversity decay and an "unexplained" alternative turn that into posteriors. "High" confidence needs ≥2 independent sources and no strong contradiction. |
| **Symptom vs cause is structural** | Hypotheses carry `layer: symptom|cause`; symptoms are tracked but can never be concluded as root cause. |
| **Change journal** | The broker watches Deployments/ConfigMaps/Services/HPAs (list+watch, the informer pattern) and records field-level diffs and *who* changed them (`kubectl` vs HPA vs Helm), because the API only stores current state. |
| **Model-friendly observability** | Logs are template-mined (thousands of lines → a dozen patterns); metrics come back as stats + sparkline + **onset time**, which the agent lines up against change times. |
| **Two independent security layers** | The agent pod has no credentials at all and only reaches the broker; the broker enforces scope, and RBAC enforces it again. A *compromised-model* test proves nothing gets through. |
| **Discriminating tool choice** | The planner is asked for calls whose result would *differ* between hypotheses (information gain), not confirmation. |
| **Real post-mortems as scenarios** | Each scenario reproduces the mechanism of a documented outage, with the hard parts that fooled humans (partial failures, victims ≠ culprits, amplifiers, latent bugs). |

## Scenarios

| Id | Post-mortem | Mechanism reproduced | Why it is hard |
|---|---|---|---|
| `cloudflare-2019-waf-regex` | Cloudflare, Jul 2019 | WAF rule with the original backtracking regex hot-reloaded from a ConfigMap; CPU pinned on the event loop | no rollout or restart, only a ConfigMap edit; HPA scale-out and probe failures are loud symptoms |
| `knight-2012-stale-version-flag` | Knight Capital, Aug 2012 | forgotten `pricing-legacy` (v0.9.7) behind the same Service; repurposed flag re-activates dead "PowerPeg" code | only 1 pod of 3 fails; the flag flip is the trigger, not the defect |
| `aws-s3-2017-capacity-removal` | AWS S3, Feb 2017 | typo'd label selector scales `inventory` 4→1 instead of `catalog-indexer` | nothing crashes or changes config; only a human-made replica change and CPU throttling |
| `github-conn-saturation` | GitHub 2022 (also Mailgun, incident.io) | DB_POOL_SIZE 4→30 rollout exhausts Postgres `max_connections`; inventory fails first | the failing service is not the one that changed (the PDF's own example chain) |
| `chef-2014-healthcheck-timeouts` | Chef Supermarket, Jul 2014 | aggressive deep liveness probe + Chaos Mesh 850 ms DB latency → restart storm | two real changes; the visible DB latency is the trigger, the probe is the root cause |
| `aws-ebs-2012-latent-leak` | AWS EBS, Oct 2012 | collector Service renamed; clients keep the old DNS name; unbounded telemetry buffer → OOMKilled loop | three hops and minutes between change and symptom; decisive log is in the *previous* container |

Details, reproduction notes and ground truth: [`scenarios/*/scenario.yaml`](scenarios/). An adversarial
`review-bot` runs continuously and logs prompt-injection payloads plus irrelevant warnings, so every
investigation happens with hostile noise in the data.

## Quick start

### 0. No cluster, no API key (2 minutes)
```bash
make venv                       # Python 3.11+
make test                       # 76 tests: policy, sanitizer, MCP protocol, ledger, full scripted investigations
make demo-offline REASONER=rules            # deterministic baseline on a recorded incident
make security-probe-offline                 # 14 attacks against the broker, all refused
ANTHROPIC_API_KEY=... make demo-offline     # same incident with the LLM reasoner
```

### 1. Prerequisites for the live environment
Docker, [kind](https://kind.sigs.k8s.io/) ≥ 0.24 (its CNI enforces NetworkPolicy), kubectl, Helm 3, Python 3.11+,
~8 GB RAM for Docker. One LLM key: `ANTHROPIC_API_KEY` (default model `anthropic:claude-sonnet-5-5`),
or `GOOGLE_API_KEY` with `MODEL=google_genai:gemini-2.5-flash`, or `OPENAI_API_KEY` with `MODEL=openai:gpt-4.1`.

### 2. Bring everything up
```bash
export ANTHROPIC_API_KEY=...     # stored as a Secret for the in-cluster agent
make venv && make up             # ~10 min first time: kind, Prometheus/Alertmanager/Grafana, Loki+Alloy,
                                 # Jaeger, Traefik (Ingress + Gateway API), metrics-server, Chaos Mesh, shop, kubesleuth
curl -s 'http://shop.localhost:8080/?q=tent'     # the shop through the Ingress
make ports                       # Grafana :3000 (admin/kubesleuth), Prometheus :9090, Jaeger :16686, agent :8081
```

### 3. Break it, investigate it
```bash
make scenarios                                   # list
make scenario S=github-conn-saturation           # inject; the ShopEdgeHigh5xxRate alert fires in ~2-3 min
make investigate INCIDENT="The checkout service is experiencing a sudden increase in 5xx errors."
#   -> live progress (hypotheses, tool calls, posteriors per round), then reports/<id>.md and .json
make reset                                       # back to healthy
```
Alert-driven path: Alertmanager posts firing `namespace=shop` alerts to the in-cluster agent, which
investigates on its own; browse reports at `http://localhost:8081` (`make ports`).

### 4. Evaluate and demonstrate the boundary
```bash
make eval            # every scenario: reset → inject → wait for alert → investigate → score vs ground truth
make eval-rules      # the same with the rule baseline, to see what the LLM adds
make security-demo   # RBAC matrix, no token in agent pod, NetworkPolicy reachability, broker attacks, audit log
```
Results land in `eval/results/<timestamp>/summary.md` with per-scenario reports.

## Repository map

| Path | What |
|---|---|
| `broker/` | read-only MCP server: `policy.py` (scope, PromQL scoping), `sanitize.py` (redaction, injection flags), `journal.py` (change journal), `tools.py` (11 tools), `logmine.py`, `timeseries.py`, `fixtures.py` (offline mode), `server.py` (MCP, rate limit, audit) |
| `agent/` | LangGraph agent: `investigation.py` (graph + stopping rule), `ledger.py` (hypotheses, grounded evidence, posteriors), `reasoners.py` (LLM / rules / scripted), `toolclient.py` (MCP client + firewall), `timeline.py`, `report.py`, `server.py` (Alertmanager webhook), `security_probe.py` |
| `shop/` | demo microservices with real failure mechanisms (one image, many roles) |
| `deploy/` | manifests: shop (Deployments, StatefulSet+PVC, Services, Ingress, HTTPRoute, HPA, ServiceMonitor, alert rules), kubesleuth (RBAC, NetworkPolicy, hardened pods), Jaeger |
| `cluster/` | kind config and pinned Helm values |
| `scenarios/` | six post-mortem reproductions with ground truth |
| `eval/` | harness and scorer |
| `fixtures/` | recorded incident snapshots for offline runs and tests |
| `docs/` | [technical write-up](docs/WRITEUP.md), [security model](docs/SECURITY.md), [Kubernetes concepts used here](docs/K8S_CONCEPTS.md) |

## Validation status (please read)

Verified in development: all unit, protocol and scripted end-to-end tests (76), the offline demo,
the 14-attack broker probe, the LLM code path through LangChain structured output (with a fake chat
model), all manifests against Kubernetes 1.33 schemas with kubeconform (CRDs included), every pinned
Helm chart version and the values keys used, the Chaos Mesh CRD fields, and each failure mechanism in
the shop services locally (e.g. the Cloudflare regex adds ~300 ms of CPU per request).

**Not yet verified:** a full run on a live kind cluster with a real LLM. The build environment had no
access to container registries, so images could not be pulled. Expect to tune scenario timings
(`wait_seconds`) and possibly chart values on first run; run `make eval` and commit the
`summary.md` it produces as the results table.
