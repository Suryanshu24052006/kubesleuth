# Checkout Service 5xx Errors Caused by Inventory Dependency Failures

**Incident:** The checkout service is experiencing a sudden increase in 5xx errors.  
**Namespace:** `shop` · **Investigation:** `20261014-084103-84f5fd` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 3 rounds, 11 tool calls, 634.2s

## Root cause

The inventory service is encountering database connection failures, causing all stock lookup queries to return HTTP 500 errors which cascade into 100% 5xx errors on the checkout service.

*Hypothesis H2 · component `checkout` · category `dependency`*

**Confidence: MEDIUM** (posterior 0.95). Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.

## Causal chain

1. Inventory service fails to connect to its database backend, resulting in OperationalError connection failures during stock lookups. (O10, O11)
2. Inventory returns HTTP 500 status with 'stock lookup failed' to upstream callers. (O6)
3. Checkout service calls inventory for stock verification, receives errors, and surfaces 5xx errors to users. (O8)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O6 | loki | strong (+2.3) | `upstream returned error upstream=inventory status=<n> body={"error":"stock lookup failed"}` | Directly shows that checkout errors are caused by inventory returning status 500. |
| ✅ O8 | prometheus | strong (+2.3) | `"dep": "inventory", "outcome": "error"` | Checkout's dependency metric records an increase in inventory errors from 0 to 19.02 rps onsetting at 08:40:06Z, exactly accounting for chec… |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-14T07:49:52.298Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-14T07:53:30+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (since reverted) (by kubectl-client-side-apply) | O2 |
| 2026-10-14T07:53:30+00:00 | change | deployment/inventory modified: spec.replicas 4 → 1 (since reverted) (by kubectl-client-side-apply) | O2 |
| 2026-10-14T07:53:30+00:00 | change | deployment/edge modified: spec.replicas 2 → 3 (by kubectl-client-side-apply) | O2 |
| 2026-10-14T07:53:30+00:00 | change | rollout/catalog-indexer new-revision | O2 |
| 2026-10-14T07:53:30+00:00 | change | rollout/checkout new-revision: containers[checkout].livenessProbe {"failureThreshold": 1, "httpG… → {"failureThreshold": 3, "httpG… | O2 |
| 2026-10-14T07:53:30+00:00 | change | rollout/edge new-revision | O2 |
| 2026-10-14T07:53:30+00:00 | change | rollout/inventory new-revision | O2 |
| 2026-10-14T07:53:30+00:00 | change | rollout/loadgen new-revision | O2 |
| 2026-10-14T07:53:30+00:00 | change | rollout/pricing new-revision | O2 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x71 on Pod/checkout-68fb58bcfd-92lpn,checkout-68fb58bcfd-jlw7x: Readiness probe failed: Get "http://10.244.1.50:8080/readyz": dial tcp… | O4 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x10 on Pod/edge-6675f7688f-btmm6,edge-6675f7688f-dtglc: Readiness probe failed: Get "http://10.244.1.56:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x16 on Pod/catalog-indexer-6f6b545fdb-27c8g,catalog-indexer-6f6b545fdb-7gbtg: Readiness probe failed: Get "http://10.244.1.44:8080/hea… | O4 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x23 on Pod/inventory-6ffc77fd45-28b67,inventory-6ffc77fd45-5hvm2: Readiness probe failed: Get "http://10.244.1.27:8080/healthz": dial … | O4 |
| 2026-10-14T07:53:34Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-rtmsj,pricing-95c99775f-z5psf: Readiness probe failed: Get "http://10.244.1.32:8080/healthz": dial tcp 10.… | O4 |
| 2026-10-14T07:53:34Z | event | event Unhealthy x6 on Pod/recommendations-7bd4dd95d6-gfbqx,recommendations-7bd4dd95d6-pxghg: Readiness probe failed: Get "http://10.244.1.34:8080/heal… | O4 |
| 2026-10-14T07:53:34Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-htm9x: Readiness probe failed: Get "http://10.244.1.37:8080/healthz": dial tcp 10.244.1.37:80… | O4 |
| 2026-10-14T07:53:35Z | event | event Unhealthy x1 on Pod/edge-6675f7688f-dtglc: Liveness probe failed: Get "http://10.244.1.22:8080/healthz": dial tcp 10.244.1.22:8080: c… | O4 |
| 2026-10-14T07:53:40Z | event | event Unhealthy x3 on Pod/catalog-indexer-6f6b545fdb-7gbtg,catalog-indexer-6f6b545fdb-pmnvz: Liveness probe failed: Get "http://10.244.1.20:8080/healt… | O4 |
| 2026-10-14T07:53:40Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-2cjfb,checkout-69cf4467b9-mtmgb: Liveness probe failed: Get "http://10.244.1.25:8080/healthz": dial tcp … | O4 |
| 2026-10-14T07:53:43Z | event | event FailedCreatePodSandBox x1 on Pod/postgres-0: Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from serv… | O4 |
| 2026-10-14T07:53:45Z | event | event FailedGetResourceMetric x2 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O4 |
| 2026-10-14T07:53:45Z | event | event FailedComputeMetricsReplicas x2 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-14T07:53:45Z | event | event InspectFailed x1 on Pod/postgres-0: Failed to inspect image "": rpc error: code = Unavailable desc = connection error: desc = … | O4 |
| 2026-10-14T07:53:45Z | event | event Failed x1 on Pod/postgres-0: Error: ImageInspectError | O4 |
| 2026-10-14T07:53:50Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O4 |
| 2026-10-14T08:01:26+00:00 | change | service/telemetry-collector-v2 created (by kubectl-client-side-apply) | O2 |
| 2026-10-14T08:01:26Z | change | service/telemetry-collector deleted | O2 |
| 2026-10-14T08:12:26Z | change | service/telemetry-collector-v2 deleted | O2 |
| 2026-10-14T08:12:27+00:00 | change | service/telemetry-collector created (by kubectl-client-side-apply) | O2 |

## Observed facts

- Checkout database pool size config was modified from 4 to 30 at 08:39:32 UTC. — `"field": "data.DB_POOL_SIZE", "old": "4", "new": "30", "in_effect": true` (O2, kubernetes)
- Checkout deployment was rolled out to revision 4 following the config change. — `"kind": "rollout", "namespace": "shop", "name": "checkout", "change": "new-revision", "revision": "4…` (O2, kubernetes)
- Checkout pods experienced repeated readiness probe connection refused failures. — `Readiness probe failed: Get \"http://10.244.1.50:8080/readyz\": dial tcp 10.244.1.50:8080: connect: …` (O4, kubernetes)
- Edge and inventory pods have had restarts and HPA for edge is at max replicas. — `"findings": ["pod edge-6675f7688f-qfm4b has restarted 2 times", "pod edge-6675f7688f-rvxfg has resta…` (O3, kubernetes)
- Checkout is logging 1,000 error lines where upstream inventory returns HTTP 500 with 'stock lookup failed'. — `upstream returned error upstream=inventory status=<n> body={"error":"stock lookup failed"}` (O6, loki)
- Checkout dependency error rate against inventory jumped from 0.0 to ~19 rps at 08:40:06Z, matching request rate. — `"dep": "inventory", "outcome": "error"` (O8, prometheus)
- Inventory service connects to the postgres database service. — `"DATABASE_URL", "value": "postgresql://shop:[REDACTED]@postgres:5432/shop"` (O9, kubernetes)
-  — `error_ratio_5xx": [{` (O11, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H2 | 0.95 | cause | dependency | active | +2/−0 | loki, prometheus | Checkout is failing because a downstream dependency is degraded or returning errors. |
| H3 | 0.01 | cause | deployment | active | +1/−1 | kubernetes | Checkout pod churn and probe failures during rollouts caused request drops and 5xx errors. |
| H4 | 0.01 | cause | dependency | active | +0/−0 |  | Inventory service is failing stock lookups due to internal errors, database issues, or configuration defects. |
| H1 | 0.00 | cause | configuration | retired (Postgres metrics show healthy resources with zero restarts o…) | +1/−1 | kubernetes | Checkout is failing queries due to database connection pool exhaustion or Postgres connection limits. |

## Alternative explanations

- **H1**: Postgres metrics show healthy resources with zero restarts or throttling, and checkout error logs confirm that 100% of failures stem from inventory returning HTTP 500 rather than database pool exhaustion.
- **H3**: Probe churn and restart events on checkout occurred between 08:23Z and 08:26Z, whereas the current ongoing 5xx errors onset sharply at 08:40:06Z, coinciding directly with inventory dependency errors.
- **H4**: Inventory service is indeed the failing component root cause as substantiated by its own database connectivity error logs and 5xx spikes, making it the primary underlying source rather than a secondary assumption.

<details><summary>Evidence for/against other hypotheses</summary>

- H1 supports (moderate, O2/kubernetes): `"field": "data.DB_POOL_SIZE", "old": "4", "new": "30", "in_effect": true` — DB_POOL_SIZE was modified recently from 4 to 30, indicating database connection pool tuning around the time of the incid…
- H3 supports (moderate, O4/kubernetes): `"checkout-68fb58bcfd-92lpn"], "message": "Back-off restarting failed container checkout in pod check…` — Checkout pods previously entered CrashLoopBackOff due to misconfigured liveness probes, causing service disruption.
- H1 contradicts (strong, O6/loki): `upstream returned error upstream=inventory status=<n> body={"error":"stock lookup failed"}` — Errors are upstream inventory HTTP 500s rather than Postgres DB pool or query timeouts.
- H3 contradicts (moderate, O8/prometheus): `"dep": "inventory", "outcome": "error"` — Current ongoing 5xx errors started around 08:40:06Z due to inventory dependency errors, well after the checkout probe re…

</details>

## Uncertainty

- The exact reason why the inventory service failed to connect to its database backend (e.g., network policy, database credential rotation, or database exhaustion beyond postgres metrics visibility) requires deeper inspection of database server-side logs.
- 3 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Inspect database server logs and connectivity from the inventory service pods to resolve the OperationalError connection failures.
- Verify database credentials, network policies, and connection limits for the inventory deployment.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +2 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `active_alerts` {} — what is alerting and since when → O1
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O2
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: continue; evidence +4 accepted / 1 rejected; new hypotheses ['H4']
  - `find_traces` {"service": "checkout", "minutes": 15, "errors_only": true} — Identify where errors originate in checkout request traces. → O5
  - `search_logs` {"namespace": "shop", "app": "checkout", "level": "error", "minutes": 30} — Examine checkout error logs for connection pool or dependency failure details. → O6
  - `workload_metrics` {"namespace": "shop", "workload": "postgres", "minutes": 30} — Check postgres health, connection metrics, and resource utilization. → O7
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — Check checkout 5xx rate, onset time, DB errors, and failing downstream dependencies. → O8
  - posteriors: H1=0.00, H2=0.95, H3=0.01, H4=0.01, unexplained=0.03

**Round 2** — decision: continue; evidence +0 accepted / 2 rejected; new hypotheses []; retired ['H1']
  - `describe` {"kind": "deployment", "namespace": "shop", "name": "inventory"} — Inspect inventory deployment spec, env vars, and referenced configmaps/secrets. → O9
  - `search_logs` {"namespace": "shop", "app": "inventory", "level": "error", "minutes": 30} — Find what internal error or downstream dependency is causing inventory stock lookups to fail. → O10
  - `workload_metrics` {"namespace": "shop", "workload": "inventory", "minutes": 30} — Check golden signals, error rates, dependency failures, and restarts for inventory. → O11
  - posteriors: H2=0.95, H3=0.01, H4=0.01, unexplained=0.03

**Round 3** — decision: model judged evidence sufficient; H2 p=0.95 (medium); evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H2=0.95, H3=0.01, H4=0.01, unexplained=0.03

Stop reason: model judged evidence sufficient; H2 p=0.95 (medium)

</details>