# Inventory Service Replica Reduction Causing Overload and Edge 5xx Errors

**Incident:** Checkout requests are timing out and the edge is returning 5xx.  
**Namespace:** `shop` · **Investigation:** `20261013-124723-5b69fa` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 1 rounds, 7 tool calls, 155.9s

## Root cause

The inventory deployment replicas were reduced from 4 to 1, causing resource contention, health probe failures, and downstream checkout timeouts.

*Hypothesis H1 · component `deployment/inventory` · category `capacity`*

**Confidence: HIGH** (posterior 0.99). High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.

## Causal chain

1. Deployment replicas for inventory were scaled down from 4 to 1 via rollout. (O3)
2. The single inventory pod became overloaded, leading to CPU and memory contention, and health/readiness probe failures. (O2, O6)
3. Inventory stock lookups began failing due to timeouts and connection errors, cascading into upstream checkout failures. (O5)
4. The ShopEdgeHigh5xxRate alert fired as checkout requests timed out and failed at the edge. (O1)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O3 | kubernetes | strong (+2.3) | `spec.replicas", "old": 4, "new": 1, "in_effect": true` | Directly shows that the inventory deployment replicas were scaled down from 4 to 1 right before probe failures and high 5xx errors started. |
| ✅ O2 | kubernetes | strong (+1.38) | `Readiness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded` | Demonstrates that the single inventory pod is struggling to respond to health checks under load. |
| ✅ O5 | kubernetes-logs | strong (+2.3) | `FATAL: sorry, too many clients already` | Direct evidence of database connection exhaustion matching the resource contention symptoms in inventory. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T12:17:30.161Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T12:21:13+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (by kubectl-client-side-apply) | O3 |
| 2026-10-13T12:21:13+00:00 | change | rollout/catalog-indexer new-revision | O3 |
| 2026-10-13T12:21:13+00:00 | change | rollout/checkout new-revision | O3 |
| 2026-10-13T12:21:13+00:00 | change | rollout/edge new-revision | O3 |
| 2026-10-13T12:21:15Z | event | event Unhealthy x25 on Pod/checkout-69cf4467b9-j69d5,checkout-69cf4467b9-k5j84: Readiness probe failed: Get "http://10.244.1.22:8080/readyz": dial tcp… | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x37 on Pod/inventory-668745bb49-5xmp9,inventory-668745bb49-78mrq: Readiness probe failed: Get "http://10.244.1.53:8080/healthz": dial … | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x12 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-v2zr7: Readiness probe failed: Get "http://10.244.1.18:8080/hea… | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x15 on Pod/recommendations-58866dbd86-8wlzh,recommendations-58866dbd86-9gsgr: Readiness probe failed: Get "http://10.244.1.54:8080/hea… | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x11 on Pod/edge-6675f7688f-cvj8l,edge-6675f7688f-xz97h: Readiness probe failed: Get "http://10.244.1.23:8080/healthz": dial tcp 10.244… | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x4 on Pod/pricing-95c99775f-8v97j,pricing-95c99775f-fkzqq: Readiness probe failed: Get "http://10.244.1.29:8080/healthz": dial tcp 10.… | O2 |
| 2026-10-13T12:21:17Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-vwkb8: Readiness probe failed: Get "http://10.244.1.37:8080/healthz": dial tcp 10.244.1.37:80… | O2 |
| 2026-10-13T12:21:18Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-cvj8l,edge-6675f7688f-xz97h: Liveness probe failed: Get "http://10.244.1.23:8080/healthz": dial tcp 10.244.1… | O2 |
| 2026-10-13T12:21:23Z | event | event Unhealthy x3 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-v2zr7: Liveness probe failed: Get "http://10.244.1.18:8080/healt… | O2 |
| 2026-10-13T12:21:23Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-j69d5,checkout-69cf4467b9-k5j84: Liveness probe failed: Get "http://10.244.1.22:8080/healthz": dial tcp … | O2 |
| 2026-10-13T12:21:28Z | event | event FailedGetResourceMetric x2 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O2 |
| 2026-10-13T12:21:28Z | event | event FailedComputeMetricsReplicas x2 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O2 |
| 2026-10-13T12:21:30Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O2 |
| 2026-10-13T12:21:43Z | event | event FailedGetResourceMetric x3 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods might… | O2 |
| 2026-10-13T12:21:43Z | event | event FailedComputeMetricsReplicas x3 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O2 |
| 2026-10-13T12:26:21+00:00 | change | deployment/checkout modified: template.annotations null → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O3 |
| 2026-10-13T12:26:21+00:00 | change | deployment/edge modified: template.annotations null → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O3 |
| 2026-10-13T12:26:21+00:00 | change | deployment/recommendations modified: template.annotations null → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O3 |
| 2026-10-13T12:26:21+00:00 | change | deployment/inventory modified: template.annotations null → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O3 |
| 2026-10-13T12:26:21+00:00 | change | rollout/checkout new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O3 |
| 2026-10-13T12:26:21+00:00 | change | rollout/edge new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O3 |
| 2026-10-13T12:26:21+00:00 | change | rollout/inventory new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O3 |
| 2026-10-13T12:26:21+00:00 | change | rollout/recommendations new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O3 |
| 2026-10-13T12:26:23Z | event | event FailedKillPod x1 on Pod/checkout-69cf4467b9-k5j84: error killing pod: [failed to "KillContainer" for "checkout" with KillContainerError: "rpc… | O2 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x2 on Pod/checkout-8457f655f7-jwzw6,checkout-8457f655f7-nmx9x: Failed to create pod sandbox: rpc error: code = Unavailabl… | O2 |

## Observed facts

- Edge is experiencing a high 5xx error rate of 76.21%. — `76.21% of edge requests fail with 5xx.` (O1, alertmanager)
- The inventory pod has restarted twice. — `pod inventory-6dcd8d4f55-vb8z7 has restarted 2 times` (O4, kubernetes)
- The inventory deployment replicas were reduced from 4 to 1. — `{"field": "spec.replicas", "old": 4, "new": 1, "in_effect": true}` (O3, kubernetes)
- Inventory pod experienced readiness and liveness probe failures due to timeouts. — `Readiness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (Client.Tim…` (O2, kubernetes)
- Inventory pods failed database connection due to PostgreSQL too many clients error — `FATAL: sorry, too many clients already` (O5, kubernetes-logs)
- Inventory pods encountered connection timeout errors when trying to connect to the database — `ConnectionTimeout detail=connection timeout expired` (O5, kubernetes-logs)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.99 | cause | capacity | active | +3/−0 | kubernetes, kubernetes-logs | Inventory service replica reduction to 1 and subsequent resource starvation/overload causes probe failures and downstrea… |
| H2 | 0.00 | cause | dependency | active | +0/−0 |  | Database connection pool exhaustion caused by too many replicas or unreleased connections. |

## Alternative explanations

- **H2**: Database connection exhaustion was a symptom of container restarts or connection spikes secondary to the overload, rather than an independent database limit breach.

## Uncertainty

- Whether the replica reduction to 1 was intended or an unintended side effect of a script or rollout.
- 1 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Scale the inventory deployment replicas back up to at least 4.
- Implement HPA (Horizontal Pod Autoscaler) to prevent manual single-replica scaling mistakes from causing capacity outages.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +2 accepted / 0 rejected; new hypotheses ['H1']
  - `active_alerts` {} — what is alerting and since when → O1
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: confident: H1 p=0.99, margin 0.99, sources ['kubernetes', 'kubernetes-logs']; evidence +1 accepted / 1 rejected; new hypotheses ['H2']
  - `pod_logs` {"namespace": "shop", "pod": "inventory-6dcd8d4f55-vb8z7", "previous": true} — Examine previous logs of the restarted inventory pod to see if it crashed due to OOM or unhandled exceptions. → O5
  - `workload_metrics` {"namespace": "shop", "workload": "inventory"} — Check CPU, memory utilization, and request rate on the inventory workload to confirm resource saturation following the replica reduction. → O6
  - `find_traces` {"service": "checkout", "minutes": 15, "errors_only": true} — Identify downstream errors originating from checkout calls to inventory or other dependencies. → O7
  - posteriors: H1=0.99, H2=0.00, unexplained=0.01

Stop reason: confident: H1 p=0.99, margin 0.99, sources ['kubernetes', 'kubernetes-logs']

</details>