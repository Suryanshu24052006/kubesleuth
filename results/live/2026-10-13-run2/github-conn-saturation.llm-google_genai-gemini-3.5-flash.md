# Checkout Service 5xx Incident RCA

**Incident:** The checkout service is experiencing a sudden increase in 5xx errors.  
**Namespace:** `shop` · **Investigation:** `20261013-131618-4c02ff` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 6 rounds, 12 tool calls, 488.8s

## Root cause

The DB_POOL_SIZE configuration in checkout-config was increased from 4 to 30, which caused connection exhaustion and database operational errors in downstream inventory queries, leading to checkout failures and edge 5xx errors.

*Hypothesis H2 · component `inventory` · category `dependency`*

**Confidence: LOW** (posterior 0.54). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. ConfigMap checkout-config DB_POOL_SIZE was modified from 4 to 30, and checkout was restarted. (O4, O9)
2. The increased pool size led to excessive concurrent database connections, causing inventory service queries to fail with 'too many clients already' and operational errors. (O7, O12)
3. Inventory service returned stock lookup failures and 5xx errors to the checkout service. (O5)
4. ShopEdgeHigh5xxRate alert fired as edge services experienced high 5xx error rates due to upstream failures. (O1, O6)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O5 | kubernetes-logs | strong (+2.3) | `upstream returned error upstream=inventory status=<n> body={"error":"stock lookup failed"}` | Directly demonstrates that checkout is failing because inventory's stock lookup failed. |
| ✅ O7 | kubernetes-logs | strong (+1.38) | `FATAL: sorry, too many clients already` | Inventory is indeed returning errors due to the database connection pool exhaustion. |
| ✅ O12 | loki | strong (+2.3) | `FATAL: sorry, too many clients already` | Inventory service calls fail with database connection errors, causing it to return 500 status to checkout. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T12:17:30.161Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T12:21:15Z | event | event Unhealthy x112 on Pod/checkout-55f8c5b4bc-6ssw7,checkout-55f8c5b4bc-bqhj9: Readiness probe failed: Get "http://10.244.1.91:8080/readyz": dial tc… | O3 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x53 on Pod/edge-6675f7688f-cvj8l,edge-6675f7688f-xz97h: Readiness probe failed: Get "http://10.244.1.23:8080/healthz": dial tcp 10.244… | O3 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x65 on Pod/inventory-5577665986-4q7mj,inventory-5577665986-9g7mx: Readiness probe failed: Get "http://10.244.1.106:8080/healthz": dial… | O3 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x28 on Pod/recommendations-54c5f6ddff-7fvrl,recommendations-54c5f6ddff-8nwmm: Readiness probe failed: Get "http://10.244.1.100:8080/he… | O3 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x19 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-rpmzl: Readiness probe failed: Get "http://10.244.1.18:8080/hea… | O3 |
| 2026-10-13T12:21:23Z | event | event Unhealthy x5 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-rpmzl: Liveness probe failed: Get "http://10.244.1.18:8080/healt… | O3 |
| 2026-10-13T12:21:28Z | event | event FailedGetResourceMetric x7 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O3 |
| 2026-10-13T12:21:28Z | event | event FailedComputeMetricsReplicas x7 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O3 |
| 2026-10-13T12:21:43Z | event | event FailedGetResourceMetric x10 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods migh… | O3 |
| 2026-10-13T12:21:43Z | event | event FailedComputeMetricsReplicas x10 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resour… | O3 |
| 2026-10-13T12:26:30Z | event | event Unhealthy x34 on Pod/edge-6675f7688f-cvj8l,edge-66978949cf-2m5mj: Readiness probe failed: Get "http://10.244.1.23:8080/healthz": context deadlin… | O3 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x9 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (… | O3 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x5 on Pod/inventory-6dcd8d4f55-vb8z7: Liveness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (C… | O3 |
| 2026-10-13T12:47:02Z | event | event Unhealthy x1 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": read tcp 10.244.1.1:52866->… | O3 |
| 2026-10-13T12:50:07Z | event | event Unhealthy x1 on Pod/checkout-6cc8cb7b8c-9kcll: Readiness probe failed: Get "http://10.244.1.60:8080/readyz": context deadline exceeded (C… | O3 |
| 2026-10-13T12:54:38Z | event | event Unhealthy x3 on Pod/checkout-7d6bdccdc8-7qz6f,checkout-7d6bdccdc8-r6c2x: Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": co… | O3 |
| 2026-10-13T12:54:42Z | event | event Unhealthy x11 on Pod/checkout-7d6bdccdc8-7qz6f,checkout-7d6bdccdc8-r6c2x: Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": d… | O3 |
| 2026-10-13T12:55:16Z | event | event BackOff x17 on Pod/checkout-7d6bdccdc8-wd72m: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-wd72m_shop(41dd06… | O3 |
| 2026-10-13T12:55:16Z | event | event BackOff x3 on Pod/checkout-7d6bdccdc8-7qz6f: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-7qz6f_shop(0d8ee6… | O3 |
| 2026-10-13T12:55:17Z | event | event BackOff x18 on Pod/checkout-7d6bdccdc8-r6c2x: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-r6c2x_shop(94ba00… | O3 |
| 2026-10-13T12:59:28+00:00 | change | deployment/checkout modified: containers[checkout].livenessProbe {"failureThreshold": 1, "httpG… → {"failureThreshold": 3, "httpG… (by kubectl-client-… | O4 |
| 2026-10-13T12:59:29+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-roll… | O4 |
| 2026-10-13T12:59:29+00:00 | change | deployment/edge modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O4 |
| 2026-10-13T12:59:29+00:00 | change | deployment/recommendations modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubec… | O4 |
| 2026-10-13T12:59:29+00:00 | change | deployment/inventory modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rol… | O4 |
| 2026-10-13T12:59:29+00:00 | change | deployment/edge modified: spec.replicas 2 → 3 (by kubectl-rollout) | O4 |
| 2026-10-13T12:59:29+00:00 | change | rollout/checkout new-revision: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T12:59:29+00:00 | change | rollout/edge new-revision: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T12:59:29+00:00 | change | rollout/inventory new-revision: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… | O4 |

## Observed facts

- Alert ShopEdgeHigh5xxRate fired because 63.26% of edge requests fail with 5xx. — `63.26% of edge requests fail with 5xx.` (O1, alertmanager)
- Checkout pods are experiencing readiness probe failures due to connection refused on port 8080. — `Readiness probe failed: Get "http://10.244.1.91:8080/readyz": dial tcp 10.244.1.91:8080: connect: co…` (O3, kubernetes)
- Checkout service logs show 100 errors stating inventory stock lookup failed. — `upstream returned error upstream=inventory status=<n> body={"error":"stock lookup failed"}` (O5, kubernetes-logs)
- Inventory pod logs show PostgreSQL database returning FATAL: sorry, too many clients already. — `detail": "connection failed: connection to server at \"10.96.120.150\", port 5432 failed: FATAL: sor…` (O7, kubernetes-logs)
- Inventory 5xx error ratio rose to 1.0 starting at 13:15:10Z. — `error_ratio_5xx": [{` (O8, prometheus)
- Configmap checkout-config was updated via kubectl-patch at 13:14:46. — `"manager": "kubectl-patch", "operation": "Update", "time": "2026-10-13T13:14:46+00:00"` (O9, kubernetes)
- The inventory pod did not have a previous terminated container instance. — `previous terminated container \"inventory\" in pod \"inventory-5577665986-4q7mj\" not found` (O10, kubernetes-logs)
- Inventory service logs show Postgres connection errors stating 'too many clients already', matching the increased DB_POOL_SIZE set on checkout. — `FATAL: sorry, too many clients already` (O12, loki)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H2 | 0.54 | cause | dependency | active | +3/−0 | kubernetes-logs, loki | The inventory service is returning 500 errors for stock lookup requests, causing checkout to fail. |
| H1 | 0.45 | cause | configuration | active | +3/−0 | kubernetes, kubernetes-logs, loki | The increase of DB_POOL_SIZE from 4 to 30 in checkout-config caused checkout pods to crash or become unready due to conn… |

## Alternative explanations

- **H1**: While H1 identifies the configuration change as the root trigger, H2 captures the direct dependency failure mechanism where inventory database exhaustion surfaces as stock lookup errors affecting checkout.

<details><summary>Evidence for/against other hypotheses</summary>

- H1 supports (strong, O7/kubernetes-logs): `FATAL: sorry, too many clients already` — The increase of DB_POOL_SIZE from 4 to 30 in checkout-config on multiple pods caused total database connection exhaustio…
- H1 supports (moderate, O9/kubernetes): `"data": {"DB_POOL_SIZE": "30", "UPSTREAM_TIMEOUT_SECONDS": "2.0"}` — Confirms the exact configuration state of checkout-config where DB_POOL_SIZE was set to 30.
- H1 supports (strong, O12/loki): `FATAL: sorry, too many clients already` — Increasing checkout DB_POOL_SIZE to 30 caused excessive concurrent connections to the database from upstream services, r…

</details>

## Uncertainty

- Exact database max_connections limit to confirm the exact threshold where connection exhaustion triggers.
- 4 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Revert DB_POOL_SIZE in checkout-config back to its original value of 4 or properly tune the database max_connections limit.
- Restart checkout and inventory pods to reset connection pools.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +0 accepted / 1 rejected; new hypotheses ['H1']
  - `active_alerts` {} — what is alerting and since when → O1
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O2
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O3
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O4

**Round 1** — decision: continue; evidence +1 accepted / 1 rejected; new hypotheses ['H2']
  - `pod_logs` {"namespace": "shop", "pod": "checkout-868f44778d-2cz7k", "tail": 100} — Check why checkout pods are failing or restarting after the DB_POOL_SIZE config change. → O5
  - `workload_metrics` {"namespace": "shop", "workload": "checkout"} — Check the exact metrics and onset of 5xx or DB errors on checkout. → O6
  - posteriors: H1=0.07, H2=0.73, unexplained=0.20

**Round 2** — decision: continue; evidence +2 accepted / 0 rejected; new hypotheses []
  - `pod_logs` {"namespace": "shop", "pod": "inventory-5577665986-4q7mj", "tail": 100} — Check inventory pod logs to determine why stock lookups are failing. → O7
  - `workload_metrics` {"namespace": "shop", "workload": "inventory"} — Check inventory workload metrics for error rates and latency. → O8
  - posteriors: H1=0.19, H2=0.76, unexplained=0.05

**Round 3** — decision: continue; evidence +1 accepted / 0 rejected; new hypotheses []
  - `describe` {"namespace": "shop", "kind": "configmap", "name": "checkout-config"} — Verify the exact configuration value set for DB_POOL_SIZE. → O9
  - posteriors: H1=0.44, H2=0.53, unexplained=0.04

**Round 4** — decision: continue; evidence +0 accepted / 2 rejected; new hypotheses []
  - `pod_logs` {"namespace": "shop", "pod": "inventory-5577665986-4q7mj", "previous": true, "tail": 100} — Check previous logs of inventory pods to determine why inventory is failing stock lookups. → O10
  - `pod_logs` {"namespace": "shop", "pod": "checkout-55f8c5b4bc-6ssw7", "previous": true, "tail": 100} — Check previous crash logs of checkout pods to see if DB_POOL_SIZE=30 caused an immediate crash/OOM or database connection pool exhaustion upon startup. → O11
  - posteriors: H1=0.44, H2=0.53, unexplained=0.04

**Round 5** — decision: continue; evidence +2 accepted / 0 rejected; new hypotheses []
  - `search_logs` {"namespace": "shop", "app": "inventory", "minutes": 30} — Find all inventory log errors across pods to confirm database connection failure patterns. → O12
  - posteriors: H1=0.45, H2=0.54, unexplained=0.00

**Round 6** — decision: round budget exhausted; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.45, H2=0.54, unexplained=0.00

Stop reason: round budget exhausted

</details>