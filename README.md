# kubesleuth

[![ci](https://github.com/Suryanshu24052006/kubesleuth/actions/workflows/ci.yml/badge.svg)](https://github.com/Suryanshu24052006/kubesleuth/actions/workflows/ci.yml)
[![live-eval](https://github.com/Suryanshu24052006/kubesleuth/actions/workflows/live.yml/badge.svg)](https://github.com/Suryanshu24052006/kubesleuth/actions/workflows/live.yml)

An AI agent that investigates Kubernetes incidents and writes a root-cause analysis. Built for the
Inter IIT Tech Meet 15.0 Prepathon (Development PS).

It works like an on-call engineer: it forms competing hypotheses, gathers evidence from Kubernetes,
metrics, logs, traces and change history, and only commits to a cause when several sources agree.
When the evidence isn't there, it says so.

## Architecture

```
   Alertmanager webhook / CLI
               │
┌──────────────▼───────────────────────────────┐
│ agent (LangGraph)       no k8s credentials   │  triage → hypothesize → plan → act → assess → decide → report
└──────────────┬───────────────────────────────┘
               │ MCP, 11 read-only tools
┌──────────────▼───────────────────────────────┐
│ broker                  read-only, 1 namespace│
└──┬───────────┬───────────┬──────────┬─────────┘
 Kubernetes  Prometheus   Loki      Jaeger   (+ Alertmanager)
```

The agent talks to the LLM but has no cluster access at all. The broker is the only way into the
cluster, and it can only read one namespace. Even a fully hijacked model can do nothing but read.

## Highlights

- **No made-up evidence.** Every evidence claim must quote tool output word for word; code checks it.
- **Confidence from evidence, not the model.** Code computes probabilities; "high" needs 2+ independent sources.
- **Symptoms are never root causes.** 5xx, restarts and failed probes must be explained, not blamed.
- **Knows what changed, who changed it, and whether it's still in effect** (`DB_POOL_SIZE 4 → 30, by kubectl`).
- **Security in layers:** credential-less agent, NetworkPolicy, read-only tools, RBAC, injection flagging, audit log.
- **Frugal with the LLM:** about 6 calls per incident, with retries and model fallback on free-tier limits.

## Scenarios: six real outages

Recreated from public post-mortems ([danluu/post-mortems](https://github.com/danluu/post-mortems)), each with a known root cause:

| Scenario | Based on | Failure |
|---|---|---|
| `cloudflare-2019-waf-regex` | Cloudflare 2019 | Backtracking WAF regex pushed via ConfigMap pins the CPU |
| `knight-2012-stale-version-flag` | Knight Capital 2012 | Forgotten old deployment wakes dead code when a reused flag flips |
| `aws-s3-2017-capacity-removal` | AWS S3 2017 | Mistyped selector scales `inventory` from 4 replicas to 1 |
| `github-conn-saturation` | GitHub 2022 | DB pool size 4 → 30 exhausts Postgres; a *different* service fails |
| `chef-2014-healthcheck-timeouts` | Chef 2014 | Aggressive liveness probe + DB latency (Chaos Mesh) → restart storm |
| `aws-ebs-2012-latent-leak` | AWS EBS 2012 | Renamed Service triggers an unbounded buffer → OOMKilled loop |

A `review-bot` pod logs prompt-injection payloads during every run.

## Results (live cluster)

Three full runs on fresh GitHub-hosted machines, 36 investigations, graded strictly (the stated root cause must
name the right component **and** mechanism):

| | Baseline (rules) | LLM agent (Gemini, free tier) | Either |
|---|---|---|---|
| Correct root cause | **10 / 18** | **8 / 17** (+4 partial) | **15 / 18** |
| Security demo | passed in all 3 runs (RBAC, no credentials, network isolation, 14/14 attacks blocked) | | |

The two are complementary: the baseline wins when one recent change explains everything (S3, EBS, Knight:
9/9), the LLM when the cause must be reasoned out across sources (Chef 3/3, Cloudflare 2/3). Per-scenario
reports and the 9 problems the live runs exposed, each with its fix and test: **[results/](results/README.md)**.

## Run it

**On GitHub (no setup):** fork, optionally add a `GOOGLE_API_KEY` secret, then **Actions → live-eval → Run workflow**.

**Offline (2 minutes, no cluster or key):**
```bash
make venv && make test            # 88 tests
make demo-offline REASONER=rules  # investigate a recorded incident
make security-probe-offline       # 14 attacks against the broker
```

**Full environment** (Docker, kind ≥ 0.24, kubectl, Helm 3, Python 3.11+, ~8 GB RAM; on Windows use WSL2):
```bash
export GOOGLE_API_KEY=...   # or ANTHROPIC_API_KEY / OPENAI_API_KEY
make venv && make up        # kind + Prometheus, Loki, Jaeger, Traefik, Chaos Mesh, shop, kubesleuth (~10 min)
make scenario S=github-conn-saturation
make investigate            # report lands in reports/
make eval                   # every scenario, scored
make security-demo          # live security checks
```

## Repository

| Path | Contents |
|---|---|
| `agent/` | LangGraph agent, evidence ledger, reasoners, MCP client + firewall, reports, Alertmanager webhook |
| `broker/` | read-only MCP server: policy, redaction, change journal, 11 tools, log mining, metric onsets |
| `shop/`, `deploy/`, `cluster/` | demo microservices, Kubernetes manifests (RBAC, NetworkPolicy), kind + Helm values |
| `scenarios/`, `eval/`, `results/` | post-mortem reproductions, evaluation harness + scorer, live results |
| `docs/` | [write-up](docs/WRITEUP.md) · [security model](docs/SECURITY.md) · [Kubernetes concepts](docs/K8S_CONCEPTS.md) |

**Limits:** LLM results are bounded by the free Gemini tier, runs are on a 4-vCPU machine, and three runs per
scenario show real variance, so treat the numbers as indicative. Details in the [write-up](docs/WRITEUP.md).
