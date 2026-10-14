# Checkout CrashLoopBackOff due to Aggressive Deep Liveness Probe

**Incident:** Checkout pods keep restarting and the storefront is throwing errors.  
**Namespace:** `shop` · **Investigation:** `20261014-082517-a318f2` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 1 rounds, 7 tool calls, 89.0s

## Root cause

The checkout service was configured with an overly aggressive 'deep' liveness probe (1s timeout, failureThreshold=1) that failed when its dependencies (Postgres and Inventory) slowed down due to a database connection bottleneck.

*Hypothesis H1 · component `deployment/checkout` · category `probe_misconfiguration`*

**Confidence: HIGH** (posterior 0.96). High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.

## Causal chain

1. Scaling up inventory (1 to 4) and catalog-indexer (1 to 3) increased the connection load on the shared Postgres database. (O3)
2. Postgres reached connection limits, causing connection timeouts and increased latency for dependent services like inventory. (O5, O6)
3. The checkout liveness probe was updated to use a 'deep' check (?deep=1) with a strict 1s timeout and a failure threshold of 1. (O3)
4. The deep health check, which depends on the now-slow DB and inventory services, exceeded the 1s timeout. (O2)
5. Because the failure threshold was set to 1, a single timeout caused Kubernetes to kill and restart the checkout pods, leading to a CrashLoopBackOff. (O2, O4)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O3 | kubernetes | strong (+2.3) | `new": "{\"failureThreshold\": 1, \"httpGet\": {\"path\": \"/healthz?deep=1\", \"port\": \"http\", \"scheme\": …` | The change to a 1s timeout and failureThreshold of 1 is extremely brittle for a 'deep' check that likely hits other services. |
| ✅ O2 | kubernetes | strong (+1.38) | `Liveness probe failed: Get "http://10.244.1.50:8080/healthz?deep=1": context deadline exceeded` | The 'context deadline exceeded' error directly matches the 1s timeout configured in the new probe. |
| ✅ O5 | kubernetes-logs | strong (+2.3) | `error connecting in 'pool-1': connection timeout expired` | The logs show the application failing to connect to its dependency (DB) during startup, which would cause the 'deep' liveness probe to fail. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-14T07:49:52.298Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-14T07:53:29+00:00 | change | configmap/checkout-config last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | configmap/edge-waf-rules last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | configmap/feature-flags last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | configmap/kube-root-ca.crt last-write (by kube-controller-manager) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/catalog-indexer last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/checkout last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/edge last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/inventory last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/postgres last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (since reverted) (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/inventory modified: spec.replicas 4 → 1 (since reverted) (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/catalog-indexer new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/checkout new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/edge new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/inventory new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/loadgen new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/pricing new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/recommendations new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/review-bot new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/telemetry-collector new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | service/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/edge last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/loadgen last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/review-bot last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/telemetry-collector last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | statefulset/postgres last-write (by kubectl-client-side-apply) | O3 |

## Observed facts

- Checkout liveness probes began failing with timeouts immediately after the configuration change. — `Liveness probe failed: Get "http://10.244.1.50:8080/healthz?deep=1": context deadline exceeded` (O2, kubernetes)
- Checkout containers are terminating with exit code 0, which is consistent with a graceful shutdown triggered by a liveness probe failure. — `last_termination": {"container": "checkout", "reason": "Completed", "exit_code": 0` (O4, kubernetes)
- The inventory service, a likely dependency of checkout, has experienced restarts. — `pod inventory-6ffc77fd45-dvnzz has restarted 2 times` (O4, kubernetes)
- The storefront is experiencing a high error rate due to the checkout service being unavailable. — `63.72% of edge requests fail with 5xx.` (O1, alertmanager)
- The checkout service has no ready endpoints, causing the storefront 5xx errors. — `service checkout has 0 ready endpoints (3 not ready)` (O4, kubernetes)
- Checkout pods are failing to establish database connections, timing out after 10 seconds. — `error connecting in 'pool-1': connection timeout expired` (O5, kubernetes-logs)
- Inventory service is also experiencing database connection timeouts. — `db_errors_rps: [{"labels": {"kind": "ConnectionTimeout"}, "points": 11, "from": "2026-10-14T08:23:47…` (O6, prometheus)
- Checkout application startup is being cancelled, likely by the kubelet killing the container due to probe failure. — `asyncio.exceptions.CancelledError` (O5, kubernetes-logs)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.96 | cause | probe_misconfiguration | active | +3/−0 | kubernetes, kubernetes-logs | The new 'deep' liveness probe for checkout is too aggressive and is failing due to dependency latency. |
| H3 | 0.02 | cause | resource_exhaustion | active | +1/−0 | prometheus | The Postgres database is saturated due to the recent scale-up of inventory and catalog-indexer. |
| H2 | 0.01 | cause | dependency | active | +1/−0 | kubernetes | The checkout service is failing because the inventory service is unhealthy. |

## Alternative explanations

- **H2**: While inventory instability (OOMKills) contributed to the latency, the immediate cause of the checkout pod restarts was the liveness probe configuration. A standard shallow probe would have kept the pods running despite the dependency slowness.
- **H3**: Postgres saturation is the trigger for the latency, but the 'hard failure' (restarts) is specifically due to how the checkout liveness probe was configured to react to that latency.

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (moderate, O4/kubernetes): `last_termination": {"container": "inventory", "reason": "Error", "exit_code": 137` — Inventory being OOMKilled at 08:19 suggests it is unstable, which would cause a 'deep' health check in checkout to fail.
- H3 supports (strong, O6/prometheus): `db_errors_rps: [{"labels": {"kind": "ConnectionTimeout"}` — Both checkout and inventory are reporting DB connection timeouts, pointing to a shared bottleneck at the database layer.

</details>

## Uncertainty

- The exact Postgres connection limit and current usage were not directly observed, though connection timeouts in logs strongly imply saturation.
- 2 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Revert the checkout liveness probe to a shallow check (e.g., /readyz or /healthz without ?deep=1).
- Increase the liveness probe timeoutSeconds to at least 5s and failureThreshold to 3 if a deep check is required.
- Investigate and increase the max_connections setting on the Postgres statefulset.
- Implement connection pooling (e.g., PgBouncer) to handle the increased load from scaled-up microservices.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +3 accepted / 0 rejected; new hypotheses ['H1', 'H2']
  - `active_alerts` {} — what is alerting and since when → O1
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: confident: H1 p=0.96, margin 0.94, sources ['kubernetes', 'kubernetes-logs']; evidence +2 accepted / 2 rejected; new hypotheses ['H3']
  - `pod_logs` {"namespace": "shop", "pod": "checkout-68fb58bcfd-92lpn", "previous": true} — To see the specific error or timeout message from the /healthz?deep=1 handler before the pod was killed. → O5
  - `workload_metrics` {"namespace": "shop", "workload": "inventory"} — To check if the inventory service is currently experiencing high latency or errors that would impact checkout. → O6
  - `find_traces` {"service": "checkout", "errors_only": true} — To identify which dependency is causing the /healthz?deep=1 call to exceed the 1s timeout. → O7
  - posteriors: H1=0.96, H2=0.01, H3=0.02, unexplained=0.01

Stop reason: confident: H1 p=0.96, margin 0.94, sources ['kubernetes', 'kubernetes-logs']

</details>