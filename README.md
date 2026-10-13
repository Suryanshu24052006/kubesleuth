# kubesleuth

[![ci](https://github.com/Suryanshu24052006/kubesleuth/actions/workflows/ci.yml/badge.svg)](https://github.com/Suryanshu24052006/kubesleuth/actions/workflows/ci.yml)
[![live-eval](https://github.com/Suryanshu24052006/kubesleuth/actions/workflows/live.yml/badge.svg)](https://github.com/Suryanshu24052006/kubesleuth/actions/workflows/live.yml)

An AI agent that investigates Kubernetes incidents and writes a root-cause analysis, built for the
Inter IIT Tech Meet 15.0 Prepathon (Development PS).

When something breaks in a cluster, the error you see is rarely where the problem started. A 5xx at
the edge might really be a config change three services away, made ten minutes earlier. I wanted an
agent that works the way a good on-call engineer does: look around, come up with a few possible
explanations, check the ones that can be told apart, and only commit to an answer when the evidence
from several places agrees. If the evidence isn't there, it should say so.

## How it's put together

There are two pieces, and keeping them apart is the most important design decision in the project.

```
            Alertmanager webhook / CLI / HTTP
                          │ incident
┌─────────────────────────▼──────────────────────────┐
│ agent (LangGraph)            no k8s credentials    │
│  triage → hypothesize → plan → act → assess → decide ──► RCA report
│            ▲                                       │
│            └──────────────── loop ─────────────────┘
└─────────────────────────┬──────────────────────────┘
                          │ MCP, 11 read-only tools
┌─────────────────────────▼──────────────────────────┐
│ broker                 read-only ServiceAccount    │
└──┬──────────────┬──────────────┬─────────────┬─────┘
 Kubernetes API  Prometheus     Loki          Jaeger      (+ Alertmanager)
```

The **agent** is the part that talks to the LLM. It has no Kubernetes credentials at all, not even
the client library, and its network policy only lets it reach the broker. The **broker** is a small
read-only MCP server. It is the only thing that can query the cluster and the observability stack,
and it can only read one namespace. So even if the model were completely fooled by something it read
in a log, the worst it could do is make more read-only queries.

## What I think is interesting about it

- **The agent can't make up evidence.** Every piece of evidence has to quote the tool output word for
  word, and code checks that the quote is really there. If it isn't, the claim is thrown out and
  shown in the report as rejected.
- **Confidence comes from the evidence, not from the model.** The model says whether something supports
  or contradicts a hypothesis and how strongly. The code turns that into a probability. "High"
  confidence needs at least two independent sources agreeing and nothing strongly against it.
- **Symptoms and causes are kept apart.** Restarts, failed probes and 5xx errors are tracked as things
  that need explaining, and the agent is never allowed to report one of them as the root cause.
- **It knows what changed and who changed it.** Kubernetes only stores the current state of an object,
  so the broker watches Deployments, ConfigMaps, Services and HPAs and records field-level diffs,
  like `DB_POOL_SIZE 4 → 30 (by kubectl)`.
- **The data is shaped for reasoning.** Thousands of log lines get grouped into a handful of
  patterns, and each metric comes back with the time it started going wrong, so the agent can check
  whether a change happened *before* the problem.
- **It asks useful questions.** When choosing what to query next, the agent is asked for queries whose
  answer would be different depending on which explanation is true, not ones that just confirm its
  current favourite.

## The failure scenarios

Instead of inventing failures, I recreated six real outages from public post-mortems (mostly from
[danluu/post-mortems](https://github.com/danluu/post-mortems)). Each one has a known root cause so the
agent's answer can be scored, and each keeps the part that made the real incident hard to diagnose.

| Scenario | Based on | What happens | Why it's tricky |
|---|---|---|---|
| `cloudflare-2019-waf-regex` | Cloudflare, July 2019 | A WAF rule with Cloudflare's original regex is pushed through a ConfigMap; it backtracks badly and pins the CPU | No deploy or restart, just a ConfigMap edit. The autoscaler maxing out looks like the problem but isn't |
| `knight-2012-stale-version-flag` | Knight Capital, 2012 | An old deployment left behind the same Service wakes up dead code when a reused feature flag is turned on | Only one pod in three fails, and the flag is the trigger, not the bug |
| `aws-s3-2017-capacity-removal` | AWS S3, Feb 2017 | A mistyped label selector scales `inventory` from 4 replicas to 1 | Nothing crashes and no config changes, only a replica count edited by a person |
| `github-conn-saturation` | GitHub 2022, also Mailgun and incident.io | Raising a DB pool size from 4 to 30 uses up all Postgres connections | The service that fails (inventory) isn't the one that changed (checkout) |
| `chef-2014-healthcheck-timeouts` | Chef, July 2014 | An aggressive liveness probe plus a little DB latency from Chaos Mesh causes a restart storm | Two real changes, and the visible one (DB latency) isn't the root cause |
| `aws-ebs-2012-latent-leak` | AWS EBS, Oct 2012 | A renamed telemetry Service triggers an unbounded buffer, then OOMKilled crash loops | Three hops and several minutes between cause and symptom; the key log is in the crashed container |

There's also a `review-bot` pod that keeps writing prompt-injection messages and irrelevant warnings
into its logs, so every investigation has hostile noise to deal with.

## Running it

### Without a cluster (about 2 minutes)
```bash
make venv                                   # needs Python 3.11+
make test                                   # 76 tests
make demo-offline REASONER=rules            # runs on a recorded incident, no API key needed
make security-probe-offline                 # throws 14 attacks at the broker
ANTHROPIC_API_KEY=... make demo-offline     # same incident, with the LLM
```

### The full environment
You'll need Docker, [kind](https://kind.sigs.k8s.io/) 0.24 or newer, kubectl, Helm 3, Python 3.11+,
about 8 GB of RAM for Docker, and one LLM key: `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY` with
`KUBESLEUTH_MODEL=google_genai:gemini-3.8-flash`, or `OPENAI_API_KEY` with `KUBESLEUTH_MODEL=openai:gpt-4.1`.
On Windows, run everything inside WSL2.

```bash
export ANTHROPIC_API_KEY=...
make venv && make up          # first run takes ~10 minutes: kind, Prometheus, Alertmanager, Grafana,
                              # Loki, Jaeger, Traefik, metrics-server, Chaos Mesh, the shop and kubesleuth
curl -s 'http://shop.localhost:8080/?q=tent'
make ports                    # Grafana :3000 (admin/kubesleuth), Prometheus :9090, Jaeger :16686, agent :8081
```

Break something and let the agent find it:
```bash
make scenarios
make scenario S=github-conn-saturation     # the alert fires after 2-3 minutes
make investigate INCIDENT="The checkout service is experiencing a sudden increase in 5xx errors."
make reset
```
You'll see the hypotheses, tool calls and probabilities round by round, and the report ends up in
`reports/`. The agent also runs on its own when Alertmanager fires; those reports are at
`http://localhost:8081`.

To score every scenario and check the security boundary:
```bash
make eval            # reset, inject, wait for the alert, investigate, score, for every scenario
make eval-rules      # same thing with the simple rule-based baseline, for comparison
make security-demo   # RBAC, credentials, network policy and broker attack checks on the live cluster
```

## Where things are

| Path | What's in it |
|---|---|
| `agent/` | the LangGraph agent: the investigation loop, the evidence ledger, the LLM and rule-based reasoners, the MCP client with its firewall, timeline and report building, the Alertmanager webhook |
| `broker/` | the read-only MCP server: access policy, redaction and injection flagging, the change journal, the 11 tools, log pattern mining, metric onset detection, offline mode |
| `shop/` | the demo microservices; each failure is a real mechanism, not a "return 500" switch |
| `deploy/` | Kubernetes manifests for the shop, kubesleuth (RBAC, network policies, hardened pods) and Jaeger |
| `cluster/` | the kind config and pinned Helm values |
| `scenarios/` | the six post-mortem reproductions and their ground truth |
| `eval/` | the evaluation harness and scorer |
| `fixtures/` | recorded incidents for offline runs and tests |
| `docs/` | [write-up](docs/WRITEUP.md), [security model](docs/SECURITY.md), [Kubernetes concepts used](docs/K8S_CONCEPTS.md), and a [sample report](docs/sample-report-rules-offline.md) |

## What has and hasn't been tested

Tested so far: all 76 unit, protocol and end-to-end tests (including one that simulates a fully
hijacked model), the offline demo, all 14 broker attacks being blocked, the LLM path through
LangChain's structured output, every manifest against the Kubernetes 1.33 schemas, every pinned Helm
chart version and the values I set, and each failure mechanism in the shop services on its own (the
Cloudflare regex adds about 300 ms of CPU per request).

Not tested yet: a complete run on a live kind cluster with a real LLM. I couldn't pull container
images where I was building this, so the first `make up` may need some tuning of scenario timings or
chart values. Running `make eval` will produce the results table, which I'll add here.
