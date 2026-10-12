# kubesleuth — technical write-up

## 1. Architecture

Three trust zones, two processes, one protocol.

| Component | Runs as | Holds | Can reach |
|---|---|---|---|
| **agent** (Python, LangGraph) | pod in `kubesleuth`, no service-account token, PSS *restricted* | LLM API key only | broker :8090, DNS, internet :443 (LLM) |
| **broker** (Python, MCP server) | pod in `kubesleuth`, SA `kubesleuth-broker` | read-only RBAC in `shop` + nodes | kube-apiserver, Prometheus, Alertmanager, Loki, Jaeger |
| **cluster + observability** | kind; Helm: kube-prometheus-stack, Loki + Alloy, Traefik, metrics-server, Chaos Mesh; Jaeger manifest | — | — |

The agent and broker are separate images with disjoint dependencies: the agent image does not even
contain a Kubernetes client library, the broker image contains no LLM library. They speak **MCP over
streamable HTTP**. Investigations start from the CLI, an HTTP call, or an **Alertmanager webhook**
(alerts with `namespace=shop` are routed to the agent).

## 2. Agent design

The loop is an explicit LangGraph state machine:

```
triage → hypothesize → plan → act → assess → decide ─┬─► hypothesize   (next round)
(fixed)     (LLM)     (LLM) (MCP)  (LLM+code) (code)  └─► report
```

* **triage** is deterministic and cheap: active alerts, namespace overview (with computed findings),
  recent changes, warning events. Every investigation starts from the same broad picture.
* **hypothesize** proposes *competing* hypotheses across mechanisms, each with a `layer`
  (cause/symptom), a category, a mechanism, and *predictions* ("if true, Loki shows X after time T").
* **plan** chooses up to 4 tool calls per round, explicitly asked for **discriminating** calls (whose
  results would differ between the top hypotheses).
* **act** runs approved calls concurrently through the firewall and the MCP client; results become
  numbered observations (`O7`). Duplicate calls are skipped.
* **assess** reads the new observations (fenced as untrusted data) and emits facts and evidence items
  (`H2 supports/contradicts, strength, verbatim quote from O7`). When new hypotheses appear, earlier
  observations are re-shown so late hypotheses get tested against early data.
* **decide** (code only) recomputes posteriors and stops when confidence is *high*, when the model and
  the ledger agree evidence is sufficient, when no new evidence arrives for two rounds, or when the
  round/tool budget (6 rounds, 26 calls) is spent.
* **report** writes the narrative; numbers, citations and the timeline come from code.

Context engineering (following Anthropic's *Effective context engineering for AI agents*): the
planner sees a one-line **digest** per observation; full payloads are shown once, to the assessor;
the timeline is extracted deterministically from structured fields.

The same graph runs three reasoners: `LLMReasoner` (any LangChain chat model via structured output:
Anthropic, Gemini, OpenAI, Ollama), `RuleReasoner` (deterministic SRE heuristics, used as an
evaluation baseline and for keyless demos), and `ScriptedReasoner` (tests, including a hijacked model).

## 3. Tooling approach

One MCP server, 11 read-only tools, all annotated `readOnlyHint`:

| Tool | Source | Returns |
|---|---|---|
| `active_alerts` | Alertmanager | what fires, since when |
| `cluster_overview` | k8s | **findings** (OOMKilled, CrashLoop, not-ready pods, Services matching no pods / 0 endpoints, Services routing to several workloads with different images, HPA at max, unbound PVCs) + workloads, pods, services, HPAs, PVCs |
| `recent_changes` | k8s | change journal diffs + rollout history from ReplicaSets + managedFields writers |
| `get_events` | k8s | events grouped by reason/object with first/last seen |
| `describe` | k8s | trimmed spec/status + write history (Secrets impossible) |
| `pod_logs` | k8s | template-mined logs, `previous=true` for crashed containers |
| `search_logs` | Loki | template-mined logs across pods incl. deleted ones; LogQL built by the broker |
| `workload_metrics` | Prometheus | golden signals + CPU throttling + memory vs limit + restarts + DB errors, with onsets |
| `query_metrics` | Prometheus | free PromQL, scope-checked |
| `find_traces` | Jaeger | **error origins** (deepest failing span), slowest traces, self-time per service |
| `service_map` | Jaeger | dependency edges |

**Why a custom broker instead of plugging in mcp-grafana / prometheus-mcp / loki-mcp directly?**
Those servers are excellent for humans but expose broader capabilities (mcp-grafana includes
dashboard/annotation write tools, generic query tools take any namespace) and return raw payloads.
The broker gives one place to enforce scope, redact, flag injections, rate-limit and audit, and
to return *analysis-ready* results (findings, mined templates, onsets, error origins). Fronting those
upstream servers through the broker with a tool allowlist is listed under *next steps*.

**Why Python rather than client-go?** The broker uses the official Python client, which wraps the same
REST API and list/watch semantics as client-go (the change journal is the informer pattern). Keeping one
language made it possible to test every component, including the MCP protocol, in one suite.

## 4. Observability sources and why

| Source | Used for | Decisive in |
|---|---|---|
| Kubernetes API (state, events, ReplicaSets, managedFields) | health, restarts and termination reasons, selectors/endpoints, rollouts | Knight (2 workloads behind 1 Service), EBS (OOMKilled), S3 (replica change by `kubectl`) |
| Change journal (watch) | field-level diffs + actor | GitHub (DB_POOL_SIZE 4→30), Chef (probe diff), Cloudflare (ConfigMap rule), EBS (Service deleted) |
| Prometheus (app metrics, cAdvisor, kube-state-metrics) | onsets, per-pod errors, throttling, memory vs limit | S3 (throttling), Knight (errors by pod), Cloudflare (CPU/latency onset) |
| Loki (via Alloy, API-tailed) | error templates across pods, including ones already gone | GitHub (`too many clients`), EBS (telemetry buffer warnings) |
| Jaeger (OTLP from every service) | error origin and latency per hop | walking from edge 5xx to the failing dependency in every scenario |
| Alertmanager | incident start, trigger | all |

## 5. How hypotheses are handled

The **ledger** is the agent's belief state, owned by code.

* Each evidence item adds a fixed weight to the hypothesis' score: weak 0.5, moderate 1.2,
  strong 2.3 (negative when it contradicts).
* **Grounding:** the quote must be a verbatim substring of the cited observation (whitespace and JSON
  escaping normalised). Otherwise the claim is rejected and reported, never scored.
* **No double counting:** one observation counts once per hypothesis and stance.
* **Source diversity:** the k-th item from the same source is discounted by 0.6^k, so ten log lines
  never outweigh logs + metrics + a config diff.
* **Posterior** = softmax over active hypotheses plus a constant "unexplained" alternative (score 1.0),
  so an untested story cannot be certain.
* **Confidence:** *high* needs p ≥ 0.8, ≥3 supporting items from ≥2 sources, no strong contradiction
  and a margin ≥ 0.35 over the runner-up; *medium* p ≥ 0.55; *low* p ≥ 0.35; else *inconclusive*.
* **Symptoms** are tracked (they need explaining) but cannot be concluded.
* Re-proposed hypotheses are merged (same component + category, similar statement).

When sources disagree the contradicting evidence lowers the posterior and is listed in the report;
the report's *Uncertainty* section always names what remains unknown.

## 6. Security and sandboxing model

Summary (full threat model and the evidence for each claim: [SECURITY.md](SECURITY.md)):

1. **No credentials where the model runs.** Agent pod: `automountServiceAccountToken: false`, no RBAC,
   PSS restricted, read-only root FS, non-root, all capabilities dropped, seccomp RuntimeDefault.
2. **Network confinement.** Default-deny NetworkPolicy; the agent may reach only the broker, DNS and
   port 443 outside private ranges (LLM API). It cannot reach the API server or Prometheus directly.
3. **Capability by construction.** The broker exposes 11 read-only tools; there is no exec, write,
   shell, URL fetch or Secret read to misuse. Backend URLs are fixed (no SSRF); LogQL is built by the
   broker with escaped literals; PromQL must pin every selector to an allowed namespace.
4. **Scope enforced twice.** Broker policy (namespace allowlist, kind allowlist, identifier
   validation, window/size limits, rate limit) and RBAC (RoleBinding in `shop` only).
5. **Agent-side firewall.** Unknown tools, out-of-scope namespaces and oversized arguments are blocked
   before leaving the process and recorded as security events.
6. **Untrusted data handling.** Broker redacts credential-shaped strings and flags instruction-like
   text; the agent fences observations with a per-investigation random marker and the model is told
   fenced content is data. Even a fully obeyed injection can only cause read-only calls inside `shop`.
7. **Audit.** Every tool call (args, outcome, bytes, latency) is logged by the broker.

Demonstrated by `make security-demo` (live) and `make security-probe-offline` / the
*compromised model* test (offline).

## 7. Known limitations

* **Live end-to-end not yet run** in development (no registry access in the build sandbox); see the
  README's validation status. Scenario wait times and chart values may need tuning.
* PromQL scoping is a careful regex analysis, not a full PromQL parser; unusual syntax may be rejected
  (fails closed) and exotic syntax could slip through. The real backstop is that Prometheus is
  read-only and the agent never reaches it directly.
* The change journal only sees changes made while the broker runs; older changes fall back to
  ReplicaSet history and managedFields timestamps without content diffs.
* Evidence weights and thresholds are hand-set, not calibrated on a large incident set.
* One namespace per investigation; no cross-cluster or cloud-provider sources.
* NetworkPolicy enforcement depends on the CNI (kindnet in kind ≥ 0.24 enforces it; the security demo
  checks this rather than assuming).
* Egress to `0.0.0.0/0:443` for the LLM API is broader than ideal; an egress proxy with an FQDN
  allowlist would tighten it.
* Operators with `kubectl port-forward` rights can reach the broker directly; that path is an
  admin capability by definition and is audited.
* The rule baseline is intentionally simple and only meant as a comparison point.

## 8. Interesting failures encountered

* **The Cloudflare regex was harmless at first.** Applied to the whole query string it matched
  quickly (an `=` appears early), so no backtracking. Real WAFs inspect each argument separately;
  doing the same made the original pattern go super-linear on long digit runs (measured: 200 digits
  ≈ 150 ms, 400 digits ≈ 2 s per evaluation).
* **PromQL scoping false positives.** The first version treated `sum` in `sum by (pod) (...)` as an
  unscoped metric name. Fixed by treating aggregation operators as keywords; covered by tests.
* **Quotes vs JSON escaping.** Models copy `"10.96.0.1"` while the payload contains `\"10.96.0.1\"`;
  verification now normalises escaping, quotes and whitespace on both sides.
* **Late hypotheses never met early evidence.** A hypothesis created in round 2 was only assessed
  against round-2 data, so the decisive config diff from triage never counted. Fixed with the
  revisit step.
* **Two definitions of "confident".** The stopping rule and the report's label briefly disagreed
  (stopped as confident, reported medium). Both now use the ledger's single definition.
* **MCP SDK v2 breaking changes** (`FastMCP` → `MCPServer`, snake_case result fields, DNS-rebinding
  host checks rejecting in-cluster host names). Versions are pinned and the allowed hosts configured.
* **Jaeger v2 listens on localhost by default**; without `JAEGER_LISTEN_HOST=0.0.0.0` no spans arrive.
* **Fixture realism:** relative timestamps embedded inside JSON log lines were not being resolved,
  which made the timeline show `@-520` instead of times; the loader now rewrites embedded ones too.

## 9. Answers to the "freedom to experiment" questions

| Question | Choice |
|---|---|
| MCP? | Yes: one curated read-only MCP server (the broker) as the only path to the cluster. |
| Direct APIs? | Inside the broker only (Kubernetes, Prometheus, Loki, Jaeger, Alertmanager HTTP APIs). |
| One agent or many? | One investigator; the separation that matters is privilege (agent vs broker), not personas. |
| Explicit hypothesis graph? | Yes: a ledger of hypotheses with grounded evidence and code-computed posteriors. |
| Summarise logs first? | Yes, deterministically (template mining), not with the LLM, so nothing is invented. |
| Timeline? | Yes, built from structured fields (changes, onsets, events, alerts, first-seen logs). |
| Dynamic queries? | Yes: golden-signal templates plus scope-checked free PromQL and filtered Loki search. |
| Historical incidents? | Not yet (next steps). |
| Traces? | Yes: error-origin analysis and per-service self time. |
| How much context? | Digest for planning, full payload once for assessment, re-show on new hypotheses. |
| What next? | Calls that discriminate between the top hypotheses. |
| Confidence? | From evidence weights, source diversity and margin, not model self-report. |
| Sandbox? | Credential-less agent + read-only broker + RBAC + NetworkPolicy + PSS restricted. |
| Sources disagree? | Contradicting evidence lowers the posterior and is surfaced in Uncertainty. |

## 10. What I would build next

1. Front `mcp-grafana`, `prometheus-mcp` and `loki-mcp` behind the broker as upstreams with a tool
   allowlist and the same sanitisation ("MCP firewall").
2. Causal edges in the ledger (H1 *explains* H3) and counterfactual checks ("if H1, pods on the old
   ReplicaSet should be healthy").
3. Retrieval of past RCAs as priors, and calibration of evidence weights on the eval set.
4. A Go/client-go version of the broker with shared informers for lower watch cost.
5. Remediation *proposals* (rollback, scale, revert ConfigMap) behind human approval, never automatic.
6. More chaos: Chaos Mesh `DNSChaos`, `PodChaos`, `StressChaos`; noisier multi-fault scenarios.
7. Egress proxy with FQDN allowlist for the LLM API.
