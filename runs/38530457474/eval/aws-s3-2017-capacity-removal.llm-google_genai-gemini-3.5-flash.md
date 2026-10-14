# Postgres Connection Exhaustion and Inventory Throttling

**Incident:** Checkout requests are timing out and the edge is returning 5xx.  
**Namespace:** `shop` · **Investigation:** `20261014-081659-5df0d9` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 2 rounds, 11 tool calls, 112.8s

## Root cause

Postgres connection pool exhaustion, likely triggered by a service rollout and the scaling down of the inventory service, which concentrated database demand and hit the max_connections limit.

*Hypothesis H4 · component `statefulset/postgres` · category `resource_exhaustion`*

**Confidence: HIGH** (posterior 0.84). High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.

## Causal chain

1. A cluster-wide rollout and scaling event reduced inventory replicas from 4 to 1 and catalog-indexer from 3 to 1. (O3)
2. The single inventory pod experienced extreme CPU throttling (over 80%) and probe failures while attempting to handle the full workload. (O1, O2, O7)
3. Postgres reached its connection limit, returning 'FATAL: sorry, too many clients already' to connecting services. (O9, O10)
4. Inventory service calls failed with OperationalErrors due to the inability to establish database connections. (O6, O10)
5. Checkout requests, dependent on inventory, timed out or failed, resulting in 5xx errors at the edge. (O1)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O6 | kubernetes-logs | strong (+2.3) | `FATAL: sorry, too many clients already` | This is the definitive error for Postgres connection exhaustion. |
| ✅ O9 | kubernetes-logs | strong (+1.38) | `FATAL: sorry, too many clients already` | Direct evidence from the database logs that the connection limit has been reached. |
| ✅ O10 | loki | strong (+2.3) | `stock lookup failed error=OperationalError detail=connection failed` | Confirms that the inventory service is a victim of the database connection exhaustion. |

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
| 2026-10-14T07:53:30+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/inventory modified: spec.replicas 4 → 1 (by kubectl-client-side-apply) | O3 |
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
| 2026-10-14T07:53:30+00:00 | change | deployment/checkout last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/edge last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/loadgen last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/review-bot last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/telemetry-collector last-write (by kubectl-client-side-apply) | O3 |

## Observed facts

- Inventory pods are experiencing extreme CPU throttling (up to 84%). — `84.76% throttling of CPU in namespace shop for container inventory in pod inventory-6ffc77fd45-28b67` (O1, alertmanager)
- Inventory pod probes are timing out with context deadline exceeded. — `Readiness probe failed: Get "http://10.244.1.30:8080/healthz": context deadline exceeded` (O2, kubernetes)
- The edge service is reporting a critical 5xx error rate of nearly 70%. — `69.22% of edge requests fail with 5xx.` (O1, alertmanager)
- An inventory pod restarted once, with the last termination reason being 'Completed' (exit 0). — `pod inventory-6ffc77fd45-dvnzz has restarted 1 times` (O4, kubernetes)
- Postgres-0 experienced container runtime errors (sandbox creation and image inspection) around 07:53. — `Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from server` (O2, kubernetes)
- Inventory service is failing to connect to Postgres because the database has reached its maximum connection limit. — `FATAL: sorry, too many clients already` (O6, kubernetes-logs)
- Jaeger is not finding any traces for the checkout service, suggesting a telemetry collection failure. — `traces_examined: 0, traces_with_errors: 0` (O8, jaeger)
- Inventory pods are failing readiness probes due to timeouts, likely caused by CPU throttling or DB connection waits. — `Readiness probe failed: Get "http://10.244.1.30:8080/healthz": context deadline` (O2, kubernetes)
- Postgres is rejecting connections because it has reached its maximum client limit. — `FATAL: sorry, too many clients already` (O9, kubernetes-logs)
- The Postgres database is configured with a default limit of 100 connections. — `selecting default max_connections ... 100` (O9, kubernetes-logs)
- The catalog-indexer service is also failing readiness probes, suggesting it is also impacted or failing. — `Readiness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1` (O2, kubernetes)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H4 | 0.84 | cause | resource_exhaustion | active | +3/−0 | kubernetes-logs, loki | Postgres connection pool exhaustion is the primary bottleneck. |
| H1 | 0.07 | cause | capacity | active | +2/−0 | alertmanager, kubernetes | Inventory service is under-provisioned after scale-down, causing checkout timeouts. |
| H2 | 0.07 | cause | dependency | active | +2/−0 | kubernetes, kubernetes-logs | Postgres database instability is causing downstream service failures. |
| H3 | 0.01 | cause | configuration | active | +1/−0 | jaeger | Telemetry collector flapping is causing network or blocking issues in app services. |
| H5 | 0.01 | cause | code_defect | active | +1/−0 | kubernetes-logs | A connection leak in the new version of inventory or checkout is exhausting the DB pool. |

## Alternative explanations

- **H1**: While inventory CPU throttling is severe, it is likely a secondary symptom of the single pod being overwhelmed; the 'too many clients' error in the database is a hard failure that would prevent checkout even if CPU were available.
- **H3**: Telemetry collector flapping explains the lack of traces in Jaeger but is unlikely to cause 5xx timeouts unless the application SDK is configured to block on telemetry export, which is less common than database-driven failures.

<details><summary>Evidence for/against other hypotheses</summary>

- H1 supports (strong, O1/alertmanager): `84.76% throttling of CPU in namespace shop for container inventory` — Extreme throttling confirms the single remaining pod cannot handle the workload.
- H1 supports (moderate, O2/kubernetes): `Readiness probe failed: Get "http://10.244.1.30:8080/healthz": context deadline exceeded` — Probe timeouts are consistent with a CPU-saturated process unable to respond in time.
- H2 supports (moderate, O2/kubernetes): `Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from server` — Runtime errors for the database pod indicate underlying infrastructure or statefulset instability.
- H2 supports (strong, O6/kubernetes-logs): `FATAL: sorry, too many clients already` — Direct error message from the inventory logs confirming Postgres is refusing connections.
- H3 supports (moderate, O8/jaeger): `traces_examined: 0, traces_with_errors: 0` — The absence of traces in Jaeger while 5xx alerts are firing strongly suggests the telemetry pipeline is broken.
- H5 supports (moderate, O9/kubernetes-logs): `first_seen": "2026-10-14T08:15:52.046379067Z"` — The 22-minute delay between the rollout (07:53) and the first connection error (08:15) is characteristic of a resource l…

</details>

## Uncertainty

- It is unclear if the connection exhaustion is purely due to high load on fewer replicas or if the new code version introduced a connection leak, given the 22-minute delay between rollout and the first fatal error.
- 4 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Increase the 'max_connections' setting in the Postgres configuration.
- Scale the inventory deployment back to 4 replicas to distribute CPU load and connection demand.
- Verify that the inventory and catalog-indexer services are correctly closing database connections in the new code version.
- Consider implementing a connection pooler like PgBouncer to manage database sessions more efficiently.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +3 accepted / 2 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `active_alerts` {} — what is alerting and since when → O1
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: continue; evidence +3 accepted / 1 rejected; new hypotheses ['H4']
  - `describe` {"kind": "deployment", "namespace": "shop", "name": "inventory"} — To check the CPU limits on the inventory deployment that are causing the 84% throttling. → O5
  - `pod_logs` {"namespace": "shop", "pod": "inventory-6ffc77fd45-dvnzz"} — To check for error messages or slow request logs in the throttled inventory pod. → O6
  - `workload_metrics` {"namespace": "shop", "workload": "inventory"} — To see if inventory latency and CPU saturation correlate with the edge 5xx rate. → O7
  - `find_traces` {"service": "checkout", "errors_only": true} — To confirm if checkout timeouts originate in the inventory service or the database. → O8
  - posteriors: H1=0.40, H2=0.40, H3=0.04, H4=0.12, unexplained=0.03

**Round 2** — decision: confident: H4 p=0.84, margin 0.77, sources ['kubernetes-logs', 'loki']; evidence +3 accepted / 1 rejected; new hypotheses ['H5']
  - `pod_logs` {"namespace": "shop", "pod": "postgres-0"} — Look for DB-side errors regarding connection limits or resource pressure. → O9
  - `search_logs` {"namespace": "shop", "contains": "too many clients"} — Determine if other services besides inventory are hitting the DB connection limit. → O10
  - `workload_metrics` {"namespace": "shop", "workload": "postgres"} — Check if Postgres is saturated and verify connection counts. → O11
  - posteriors: H1=0.07, H2=0.07, H3=0.01, H4=0.84, H5=0.01, unexplained=0.01

Stop reason: confident: H4 p=0.84, margin 0.77, sources ['kubernetes-logs', 'loki']

</details>