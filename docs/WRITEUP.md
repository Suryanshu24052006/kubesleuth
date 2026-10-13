# kubesleuth: technical write-up

This document covers what the problem statement asks for: architecture, agent design, tooling,
observability sources, how investigations and hypotheses work, the security model, known limitations,
failures I ran into, and what I'd build next.

## 1. Architecture

The system has two processes that never share credentials.

The **agent** runs the investigation and talks to the LLM. It runs in its own pod with no
service-account token and no Kubernetes permissions. I deliberately didn't even install a Kubernetes
client library in its image. A NetworkPolicy lets it reach only the broker, DNS, and port 443 on the
public internet for the LLM API.

The **broker** is a small MCP server and the only thing allowed to look at the cluster. Its
ServiceAccount can `get`, `list` and `watch` resources in the `shop` namespace and read nodes, nothing
more. It talks to the Kubernetes API, Prometheus, Alertmanager, Loki and Jaeger.

The two talk over MCP (streamable HTTP). Everything runs on a kind cluster. The observability stack and
supporting tools are installed with pinned Helm charts: kube-prometheus-stack, Loki with Alloy shipping
the logs, Traefik for Ingress and the Gateway API, metrics-server for the autoscaler, and Chaos Mesh.
Jaeger is a plain manifest. Investigations start from the command line, an HTTP call, or automatically
when Alertmanager fires an alert for the `shop` namespace.

## 2. How the agent is designed

The investigation is an explicit LangGraph state machine:

```
triage → hypothesize → plan → act → assess → decide ─┬─► hypothesize   (another round)
                                                     └─► report
```

**Triage** is the same every time and doesn't use the LLM. It pulls the active alerts, a health summary
of the namespace, recent changes and warning events. That gives the model a broad starting picture
cheaply.

**Hypothesize** keeps a set of competing explanations. Each one is marked as a cause or a symptom, gets
a category (configuration, capacity, dependency and so on), a mechanism, and predictions: what we'd
expect to see, and where, if it were true.

**Plan** picks up to four tool calls for the round. The prompt asks specifically for calls that would
come back *differently* depending on which hypothesis is right, because those are the ones that actually
narrow things down.

**Act** runs the approved calls in parallel through the firewall and MCP client. Each result is saved
with a number (O1, O2, …) so it can be cited later. Repeated identical calls are skipped.

**Assess** shows the model the new results, clearly marked as untrusted data, and asks for facts and
evidence: which hypothesis a result supports or contradicts, how strongly, and a quote copied from the
result.

**One model call per round.** With the LLM reasoner, assess, hypothesize and plan happen in a *single*
structured call: the model reads the new results, records evidence, proposes or retires hypotheses, and
chooses the next tool calls in one answer. New hypotheses are labelled N1, N2, … so evidence in the
same answer can cite them, and the code maps those labels to real ids. An investigation therefore costs
about 5–7 model calls instead of about 20, which mattered on the free Gemini tier (section 8). If that
combined call fails, the graph falls back to separate hypothesize and plan calls.

**Decide** is pure code. It recomputes the probabilities and stops when confidence is high, when the
model and the numbers both say there's enough evidence, when two rounds pass with nothing new, or when
the budget runs out (6 rounds, 26 tool calls).

**Report** writes the narrative. The numbers, citations and timeline all come from code; the model only
supplies the wording.

To keep the model's context small and useful, the planner sees a one-line summary of each result, the
full result is shown only once to the assessor, and the timeline is built directly from the data.

The same loop can run with three different "reasoners". There's the LLM one, which works with
Anthropic, Gemini, OpenAI or Ollama through LangChain. There's a simple rule-based one I use as a
baseline and for demos without an API key. And there's a scripted one used in tests, including a test
where the model is deliberately hostile.

## 3. Tools

The broker exposes eleven tools, all marked read-only:

| Tool | Reads from | What it gives back |
|---|---|---|
| `active_alerts` | Alertmanager | what's firing and since when |
| `cluster_overview` | Kubernetes | a list of problems it spotted (OOMKilled, crash loops, pods not ready, Services with no endpoints or selecting nothing, Services sending traffic to two different versions, autoscalers at their limit, unbound volumes) plus workloads, pods, Services, autoscalers and volumes |
| `recent_changes` | Kubernetes | what changed, field by field, who changed it (a person with kubectl, Helm, or a controller), and whether each change is **still in effect** or was later reverted |
| `get_events` | Kubernetes | events grouped by reason and object, with first and last seen times |
| `describe` | Kubernetes | a trimmed view of one object and its write history (Secrets are impossible to read) |
| `pod_logs` | Kubernetes | a pod's logs grouped into patterns, including the previous crashed container |
| `search_logs` | Loki | logs across all pods, including ones that are gone; the broker writes the query itself |
| `workload_metrics` | Prometheus | request rate, errors, latency, CPU throttling, memory against its limit, restarts and DB errors, each with the time it started going wrong |
| `query_metrics` | Prometheus | any PromQL query, as long as it stays inside the allowed namespace |
| `find_traces` | Jaeger | where errors actually start, the slowest requests, and time spent per service |
| `service_map` | Jaeger | which services call which |

I considered plugging in existing servers like mcp-grafana, prometheus-mcp or loki-mcp directly. They're
good tools, but they expose more than this agent should have (mcp-grafana can edit dashboards, for
example) and they return raw data. Having my own broker gave me one place to enforce scope, redact
secrets, flag injection attempts, rate-limit and log every call, and to return results that are already
summarised. Putting those servers behind the broker is on my list for later.

The broker is written in Python with the official Kubernetes client rather than Go's client-go. It uses
the same API and the same watch mechanism; I chose Python so the whole system, including the MCP
protocol itself, could be tested in one test suite.

## 4. Where the evidence comes from

| Source | What I use it for | Where it decides the outcome |
|---|---|---|
| Kubernetes API (state, events, ReplicaSets, write history) | health, restarts and why they happened, selectors and endpoints, rollouts | Knight Capital (two versions behind one Service), EBS (OOMKilled), S3 (a person changed the replica count) |
| Change journal (watch) | field-level diffs and who made them | GitHub (pool size 4 → 30), Chef (probe change), Cloudflare (new WAF rule), EBS (Service deleted) |
| Prometheus | when things started, errors per pod, CPU throttling, memory against limits | S3 (throttling), Knight Capital (errors from one pod), Cloudflare (CPU and latency) |
| Loki | error patterns across pods, including deleted ones | GitHub ("too many clients"), EBS (telemetry buffer warnings) |
| Jaeger | where errors start and how long each hop takes | following the error from the edge to the real culprit in every scenario |
| Alertmanager | when the incident started and what triggered it | all of them |

## 5. How hypotheses are handled

The agent's beliefs live in a ledger that the code controls, not the model.

Each piece of evidence moves a hypothesis' score by a fixed amount depending on its strength: 0.5 for
weak, 1.2 for moderate, 2.3 for strong, negative if it contradicts. Before any evidence counts, the code
checks that its quote really appears in the result it cites, ignoring differences in whitespace and
escaping. If it doesn't, the claim is rejected and listed in the report.

A few rules keep the scores honest. The same result can only count once for a hypothesis. Repeated
evidence from the same source counts less each time, so ten log lines can't outweigh logs, metrics and a
config diff together. The probabilities always include an "unexplained" option, so a barely tested
explanation can never look certain. High confidence needs a probability of at least 0.8, three or more
supporting pieces from at least two sources, nothing strongly against it, and a clear lead over the next
explanation. Symptoms are tracked but can never be reported as the root cause. When sources disagree,
the contradicting evidence lowers the score and shows up in the report's uncertainty section.

## 6. Security and sandboxing

The full threat model is in [SECURITY.md](SECURITY.md). In short, I assumed the model could be wrong,
manipulated, or completely taken over, and designed so that even then nothing bad can happen:

1. **No credentials where the model runs.** The agent pod has no token, no permissions and no Kubernetes
   client, and runs under Pod Security "restricted" (non-root, read-only filesystem, no capabilities).
2. **Locked-down network.** Everything in the namespace is denied by default. The agent can only reach the
   broker, DNS and the LLM API.
3. **Nothing dangerous to call.** There are no tools for running commands, writing, deleting, fetching
   URLs or reading Secrets. Backend addresses are fixed, Loki queries are built by the broker, and every
   PromQL query must stay inside the allowed namespace.
4. **Scope enforced twice.** The broker checks every request, and RBAC independently refuses anything
   outside `shop`.
5. **A firewall on the agent side.** Unknown tools, other namespaces and oversized arguments are blocked
   before the request is even sent, and each attempt is recorded in the report.
6. **Logs are treated as hostile.** The broker redacts anything that looks like a credential and flags text
   that reads like instructions. The agent fences all tool output and tells the model it's data, not
   instructions.
7. **Everything is logged.** Every tool call is written to an audit log with its outcome.

`make security-demo` checks all of this on the live cluster, and `make security-probe-offline` plus the
hijacked-model test check it without one.

## 7. Known limitations

- **The LLM results come from the free Gemini tier**, which allows a few requests per minute and about 20 per
  day per model, with frequent "overloaded" errors. The agent copes (retries, model fallback), but the
  numbers would likely improve with a paid or self-hosted model.
- **Each scenario has been run once per reasoner** on a 4-vCPU GitHub runner, so the results are indicative,
  not statistically strong, and a heavy scenario can stress the cluster itself.
- The PromQL checks use careful pattern matching rather than a real parser. If they're unsure, they
  refuse, and Prometheus is read-only anyway.
- The change journal only sees changes made while the broker is running; older ones show up without the
  exact diff.
- The evidence weights and thresholds are set by hand, not tuned on a large set of incidents.
- It investigates one namespace at a time.
- Whether network policies are enforced depends on the cluster's network plugin, which is why the security
  demo checks it instead of assuming.
- Allowing the agent out to any public address on port 443 is broader than I'd like; an egress proxy with a
  domain allowlist would be better.
- Anyone who can `kubectl port-forward` can reach the broker directly. That already requires admin-level
  access, and those calls are logged too.
- The rule-based reasoner is deliberately basic; it's only there for comparison.

## 8. Things that went wrong along the way

The most useful bugs came from the first runs on a real cluster (GitHub Actions, see section 11):

- **Live data broke the timeline.** Real tool results are much bigger than my recorded test incident,
  so the broker trimmed long lists and appended a "…N more omitted" string to them. The agent's timeline
  code then called `.get()` on that string and crashed. Lists are now trimmed without markers, recent
  changes come newest-first so trimming keeps the latest ones, and a regression test inflates the fixture
  until every result gets trimmed.
- **The eval never reached the broker.** Its `kubectl port-forward` tunnels died silently. They now
  health-check before each use, restart when needed and log to the run output.
- **The LLM model I configured had been retired.** `gemini-2.5-flash` returned 404 for new API keys. The
  agent carried on and reported "inconclusive", which hid a configuration error behind a plausible verdict.
  Unusable models (404, bad key) now stop the run with a clear error.
- **The free tier allowed 20 requests per day per model**, and the agent used three model calls per round.
  I merged assessment, hypothesis updates and planning into one call per round (about 6 calls per
  investigation instead of about 20), and the agent now moves to the next Gemini model when one model's
  daily quota runs out. The models used are listed in every report.
- **Models return near-miss JSON** ("supporting" instead of "supports", missing optional fields). Each
  rejected answer wasted a whole call, so parsing now normalises near-misses. Evidence still has to pass
  the quote check, so this leniency never affects what counts as proof.
- **The Cloudflare regex didn't break anything at first.** I was running it against the whole query
  string, which contains an `=` early on, so it matched instantly. Real WAFs check each parameter
  separately. Once I did that, the original pattern slowed down dramatically on long digit strings: about
  150 ms for 200 digits and about 2 seconds for 400.
- **My PromQL check blocked valid queries.** It treated `sum` in `sum by (pod) (...)` as a metric with no
  namespace. I fixed it by recognising aggregation keywords and added tests.
- **Quotes didn't match because of escaping.** The model would copy `"10.96.0.1"` while the data
  contained `\"10.96.0.1\"`. The check now normalises both sides.
- **Late hypotheses missed early evidence.** A hypothesis created in round two was only checked against
  round-two data, so the key config diff from the first look never counted. That's why the assess step
  now re-shows earlier results.
- **Two different ideas of "confident".** For a while the agent could stop because it felt confident and
  then label its own report as medium confidence. Both now use the same definition.
- **The MCP Python SDK changed a lot in version 2** (renamed classes, new field names, host checks that
  rejected in-cluster addresses). I pinned the versions and configured the allowed hosts.
- **Jaeger v2 only listens on localhost by default**, so no traces arrived until I set
  `JAEGER_LISTEN_HOST=0.0.0.0`.
- **Recorded test data showed placeholder times.** Relative timestamps inside JSON log lines weren't
  being converted, so the timeline showed `@-520` instead of real times.

## 9. My answers to the "freedom to experiment" questions

| Question | What I chose |
|---|---|
| Use MCP? | Yes, a single read-only MCP server that is the only way into the cluster. |
| Talk to APIs directly? | Only inside the broker. |
| One agent or several? | One investigator. The split that matters is privileges (agent vs broker), not personas. |
| Keep an explicit hypothesis graph? | Yes, a ledger of hypotheses with checked evidence and probabilities computed in code. |
| Summarise logs before the model sees them? | Yes, by grouping them into patterns in code, so nothing gets invented. |
| Build a timeline? | Yes, straight from the data: changes, metric onsets, events, alerts and first-seen errors. |
| Query metrics and logs dynamically? | Yes, through ready-made metric summaries, scope-checked PromQL and filtered log search. |
| Use past incidents? | Not yet; it's on the list below. |
| Use traces? | Yes, mainly to find where errors start and where time is spent. |
| How much context to give the model? | Short summaries for planning, full results once for assessing, earlier results re-shown when needed. |
| How to decide what to look at next? | Pick queries that would tell the leading explanations apart. |
| How to calculate confidence? | From evidence strength, how many independent sources agree, and the lead over the runner-up. |
| How to build the sandbox? | Agent without credentials, read-only broker, RBAC, network policies and Pod Security "restricted". |
| What if sources disagree? | Contradicting evidence lowers the score and is listed under uncertainty. |

## 10. What I'd build next

1. Put mcp-grafana, prometheus-mcp and loki-mcp behind the broker with an allowlist of safe tools.
2. Link hypotheses to each other ("this explains that") and check what *should* be true if each one is
   right, for example "if the new version is broken, pods on the old version should be fine".
3. Use past reports as a starting point, and tune the evidence weights on the evaluation results.
4. Rewrite the broker in Go with client-go informers to lower the cost of watching.
5. Let the agent *suggest* fixes like a rollback or reverting a ConfigMap, always waiting for a human to
   approve them.
6. Add more chaos experiments (DNS failures, pod kills, CPU stress) and scenarios with several faults at
   once.
7. Route the agent's internet access through an egress proxy that only allows the LLM provider's domain.

## 11. Results and continuous live evaluation

The first complete live run: the rule-based baseline found the correct root cause in **3 of 6** scenarios
and the LLM agent in **2 of 5** (the sixth could not run because the free daily quota was used up). The
security demo passed every check on the live cluster. The LLM found the two causes that need reasoning
across sources (the exact Cloudflare WAF rule; the Chef-style aggressive liveness probe). The baseline won
where one recent change explains everything. Per-scenario reports and the problems the run exposed are in
[results/](../results/README.md).


Two GitHub Actions workflows keep the project honest:

- **ci** (every push): all tests, the offline investigation, the 14-attack broker probe, shell-script
  checks and manifest validation against the Kubernetes 1.33 schemas.
- **live-eval** (on demand): a fresh GitHub-hosted machine creates the kind cluster with `make up`,
  runs the security demo against the live cluster, then for every scenario resets the shop, injects the
  failure, waits for Alertmanager, and lets both the rule-based baseline and the LLM agent investigate the
  same incident. Each RCA is scored against the scenario's ground truth. Results, reports, logs and
  diagnostics are kept in the repository (`results/` and the `ci-output` branch), so every number in the
  README can be traced back to a run.
