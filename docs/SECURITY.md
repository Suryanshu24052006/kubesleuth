# Security model

## Assumptions

* The LLM may be wrong, manipulated by data it reads (prompt injection), or fully hijacked.
  The design must stay safe **even if every model output is adversarial**.
* Anything a workload can influence is untrusted: logs, events, annotations, labels, ConfigMap
  contents, trace tags, alert label values, object names.
* The operator who runs `make` (cluster-admin on their own kind cluster) is trusted.
* Initial scope is **read-only investigation of one namespace** (`shop`).

## Boundary: what the agent can and cannot do

| | Can | Cannot |
|---|---|---|
| Kubernetes | read pods, logs, events, deployments, replicasets, statefulsets, services, endpointslices, configmaps, PVCs, HPAs, ingresses, networkpolicies in `shop`; read nodes | read Secrets or ServiceAccounts; exec, port-forward, attach; create/update/patch/delete/scale anything; read any other namespace |
| Metrics | PromQL with every selector pinned to `shop` (or node-level metrics) | unscoped, other-namespace, regex-widened or negative-namespace queries; admin API |
| Logs | Loki queries the broker builds from validated labels and an escaped literal filter | raw LogQL, other namespaces |
| Traces | Jaeger traces/dependencies for named services | arbitrary URLs |
| Network (agent pod) | broker :8090, DNS, :443 outside private ranges | kube-apiserver, Prometheus, Loki, Postgres, any pod |
| Host | nothing | no hostPath, no privileges, no capabilities, read-only root FS |

## Layers (each independent of the others)

1. **Credential-less agent.** `automountServiceAccountToken: false`, no RBAC binding, and no Kubernetes
   client in the image. A hijacked agent process has nothing to authenticate with.
2. **NetworkPolicy.** Default deny in `kubesleuth`; explicit egress for agent → broker/DNS/443-public and
   broker → API server/observability; broker ingress only from the agent.
3. **Pod hardening.** Namespace labelled Pod Security Standard `restricted`: non-root, no privilege
   escalation, all capabilities dropped, seccomp RuntimeDefault, read-only root filesystem.
4. **Broker = capability boundary.** Only 11 read-only tools exist. Schema validation rejects malformed
   arguments before code runs; policy rejects out-of-scope namespaces, forbidden kinds, invalid names,
   oversized windows, unscoped PromQL. Backends are fixed URLs (no SSRF). Token-bucket rate limit.
5. **RBAC.** `get/list/watch` only, bound by RoleBinding in `shop` (plus read-only `nodes`). If broker
   policy had a bug, the API server would still refuse.
6. **Agent-side firewall.** Only broker-advertised read-only tools; namespace pinned to the investigation;
   argument size limit; every block recorded as a security event in the report.
7. **Output hygiene.** Broker redacts credential-shaped strings (URLs with passwords, bearer tokens,
   JWTs, cloud keys, private keys, sensitive ConfigMap keys; the change journal stores only hashes of
   sensitive values) and flags instruction-like text with its location.
8. **Prompt structure.** Observations are fenced with a random per-investigation marker the data cannot
   close; the system prompt states fenced content is data; flagged content carries an explicit warning.
9. **Grounding.** Conclusions can only rest on verbatim, machine-checked quotes, so injected text
   saying "the root cause is DNS" cannot become evidence unless it is literally in the data, and even then it
   is weighed like any other single-source claim and surfaced in Security notes.
10. **Audit.** Each broker call logs tool, arguments, outcome (ok/denied/backend_unavailable/rate_limited),
    bytes and latency.

## Demonstrations

| Check | How | Expected |
|---|---|---|
| RBAC matrix (15 checks) | `make security-demo` (`kubectl auth can-i --as system:serviceaccount:kubesleuth:kubesleuth-broker`) | reads in `shop` yes; secrets/exec/port-forward/writes/other namespaces no |
| No credentials in agent | same; checks token file and absence of the client library | absent |
| Network confinement | same; HTTP from inside the agent pod to broker, API server, Prometheus, Loki, Postgres | only broker succeeds |
| Broker policy (14 attacks) | `make security-probe-offline` or via the live demo | every attack refused, legitimate read allowed |
| Compromised model | `agent/tests/test_investigation.py::test_compromised_model_stays_inside_the_boundary` | exec tool, other namespace, Secret read, unscoped PromQL all blocked; fabricated evidence rejected; verdict inconclusive |
| Prompt injection in logs | `review-bot` logs payloads continuously; fixture plants one | flagged in reports' Security notes; no behaviour change possible beyond read-only scope |

## Residual risks

* An injection could still *mislead* reasoning (e.g. waste tool budget or bias assessments). The
  grounding check, source-diversity rule and visible security notes reduce but cannot eliminate this.
* Data the agent legitimately reads is sent to the LLM provider. Redaction lowers, not removes, that
  exposure; use a self-hosted model (Ollama) for sensitive clusters.
* Egress to public :443 is broad (NetworkPolicy cannot filter by hostname); an egress proxy would fix it.
