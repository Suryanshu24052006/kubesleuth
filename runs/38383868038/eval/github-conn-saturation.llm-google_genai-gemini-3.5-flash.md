# Inventory Service Database Connection Failure Leading to Checkout 5xx Errors

**Incident:** The checkout service is experiencing a sudden increase in 5xx errors.  
**Namespace:** `shop` · **Investigation:** `20261013-112521-c805eb` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 3 rounds, 11 tool calls, 1683.2s

## Root cause

The inventory service is failing to connect to its database (OperationalError during stock lookup), returning HTTP 500 'stock lookup failed' to the checkout service which propagates up as edge 5xx responses.

*Hypothesis H2 · component `inventory` · category `dependency`*

**Confidence: MEDIUM** (posterior 0.56). Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.

## Causal chain

1. Inventory service experiences database connectivity failures (OperationalError: connection failed) when attempting stock lookups. (O10)
2. Inventory service responds with HTTP 500 and body '{"error":"stock lookup failed"}' to incoming requests from checkout. (O7, O10, O11)
3. Checkout service fails upstream dependency calls to inventory, causing checkout request failures to spike to 100%. (O5, O7, O8)
4. Edge service receives 5xx error responses from checkout, triggering the ShopEdgeHigh5xxRate alert at 69.69% error rate. (O1, O8)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O4 | kubernetes | weak (+0.5) | `"message": "Readiness probe failed: Get \"http://10.244.1.105:8080/healthz\": context deadline exceeded (Clien…` | Inventory had probe timeouts earlier, though last seen was around 11:20:56. |
| ✅ O7 | loki | strong (+2.3) | `upstream returned error upstream=inventory status=<n> body={"error":"stock lookup failed"}` | Directly confirms checkout's 5xx errors originate from inventory failing stock lookup requests. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x81 on Pod/inventory-5f7599564b-7mm8z,inventory-5f7599564b-9g5g6: Readiness probe failed: Get "http://10.244.1.105:8080/healthz": dial… | O4 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x49 on Pod/edge-555d7c4d58-d59d9,edge-555d7c4d58-g7bqs: Readiness probe failed: Get "http://10.244.1.50:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x110 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tc… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x29 on Pod/recommendations-55b5fd5477-6lbkr,recommendations-55b5fd5477-cdtzd: Readiness probe failed: Get "http://10.244.1.88:8080/hea… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x22 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Readiness probe failed: Get "http://10.244.1.19:8080/hea… | O4 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x4 on Pod/edge-6675f7688f-5jhhr,edge-6675f7688f-xnt2d: Liveness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1… | O4 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x5 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Liveness probe failed: Get "http://10.244.1.19:8080/healt… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x2 on Pod/inventory-6f6c46876d-6xqxs,inventory-6f6c46876d-9v8h6: Failed to create pod sandbox: rpc error: code = Unavaila… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x2 on Pod/inventory-6ffc77fd45-6f8pt,inventory-6ffc77fd45-wc82r: error killing pod: [failed to "KillContainer" for "inventory" wit… | O4 |
| 2026-10-13T10:44:24Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc … | O4 |
| 2026-10-13T10:44:25Z | event | event FailedKillPod x1 on Pod/edge-6675f7688f-xnt2d: error killing pod: [failed to "KillContainer" for "edge" with KillContainerError: "rpc err… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/inventory-6f6c46876d-9v8h6: Liveness probe failed: Get "http://10.244.1.53:8080/healthz": dial tcp 10.244.1.53:8080: c… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/recommendations-67c55868cc-2mk82: Liveness probe failed: Get "http://10.244.1.52:8080/healthz": dial tcp 10.244.1.52:8080: c… | O4 |
| 2026-10-13T10:55:24Z | event | event FailedGetResourceMetric x6 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods might… | O4 |
| 2026-10-13T10:55:24Z | event | event FailedComputeMetricsReplicas x6 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T10:58:23Z | event | event Unhealthy x16 on Pod/inventory-5f7599564b-7mm8z,inventory-5f7599564b-svtzs: Readiness probe failed: Get "http://10.244.1.105:8080/healthz": cont… | O4 |
| 2026-10-13T10:58:32Z | event | event Unhealthy x5 on Pod/inventory-5f7599564b-7mm8z,inventory-8585795f99-wc2db: Liveness probe failed: Get "http://10.244.1.105:8080/healthz": contex… | O4 |
| 2026-10-13T11:06:04Z | onset | checkout memory_working_set_bytes[checkout-69d8947794-5qm4v] increase: 5885952.0 → 62754816.0 | O8 |
| 2026-10-13T11:06:31Z | event | event Unhealthy x3 on Pod/checkout-69d8947794-29kkk,checkout-69d8947794-5qm4v: Liveness probe failed: Get "http://10.244.1.83:8080/healthz?deep=1": co… | O4 |
| 2026-10-13T11:06:35Z | event | event Unhealthy x11 on Pod/checkout-69d8947794-29kkk,checkout-69d8947794-5qm4v: Liveness probe failed: Get "http://10.244.1.83:8080/healthz?deep=1": d… | O4 |
| 2026-10-13T11:07:04Z | onset | checkout container_restarts on 3/3 series increase: 0.0 → 3.0 | O8 |
| 2026-10-13T11:07:09Z | event | event BackOff x3 on Pod/checkout-69d8947794-29kkk: Back-off restarting failed container checkout in pod checkout-69d8947794-29kkk_shop(1c3330… | O4 |
| 2026-10-13T11:07:09Z | event | event BackOff x3 on Pod/checkout-69d8947794-5qm4v: Back-off restarting failed container checkout in pod checkout-69d8947794-5qm4v_shop(8bb9a3… | O4 |
| 2026-10-13T11:07:11Z | event | event BackOff x3 on Pod/checkout-69d8947794-j8gmg: Back-off restarting failed container checkout in pod checkout-69d8947794-j8gmg_shop(615460… | O4 |
| 2026-10-13T11:10:06+00:00 | change | deployment/checkout modified: containers[checkout].livenessProbe {"failureThreshold": 1, "httpG… → {"failureThreshold": 3, "httpG… (by kubectl-client-… | O3 |
| 2026-10-13T11:10:06+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kube-controller-manager) | O3 |
| 2026-10-13T11:10:06+00:00 | change | deployment/edge modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |
| 2026-10-13T11:10:06+00:00 | change | deployment/recommendations modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |
| 2026-10-13T11:10:06+00:00 | change | deployment/inventory modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |

## Observed facts

- Alert ShopEdgeHigh5xxRate fired critically with 69.69% of edge requests failing with 5xx. — `"alertname": "ShopEdgeHigh5xxRate", "namespace": "shop", "service": "edge", "severity": "critical"},…` (O1, alertmanager)
- checkout-config ConfigMap was modified by kubectl-patch, updating DB_POOL_SIZE from 4 to 30. — `"name": "checkout-config", "change": "modified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4…` (O3, kubernetes)
- checkout deployment underwent a rollout restart immediately following the checkout-config modification. — `"name": "checkout", "change": "modified", "fields": [{"field": "template.annotations", "old": "{\"ku…` (O3, kubernetes)
- Edge HPA is scaled to its maximum limit of 4 replicas. — `"findings": ["HPA edge is at maxReplicas (4)"]` (O2, kubernetes)
- All 1000 sampled error logs in checkout are due to upstream inventory returning HTTP 500 with 'stock lookup failed'. — `upstream returned error upstream=inventory status=<n> body={"error":"stock lookup failed"}` (O7, loki)
- Prometheus reports no DB error metrics for checkout. — `no_data: ["db_errors_rps"]` (O8, prometheus)
- Checkout container logs directly confirm status 500 responses with body 'stock lookup failed' from inventory. — `{"ts": "2026-10-13T11:30:37.859Z", "level": "error", "svc": "checkout", "version": "1.4.0", "msg": "…` (O5, kubernetes-logs)
- Inventory service errors are caused by PostgreSQL rejecting connections with 'FATAL: sorry, too many clients already'. — `stock lookup failed error=OperationalError detail=connection failed: connection to server at "<ip>",…` (O10, loki)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H2 | 0.56 | cause | dependency | active | +2/−0 | kubernetes, loki | Downstream dependency failure (such as inventory or pricing) is causing checkout to return 5xx errors. |
| H4 | 0.34 | cause | dependency | active | +1/−0 | loki | Inventory service internal failure or database error is causing it to return HTTP 500 'stock lookup failed' to checkout. |
| H1 | 0.00 | cause | configuration | retired (Checkout errors are entirely 500 responses from upstream inv…) | +2/−2 | alertmanager, kubernetes | Increasing checkout DB_POOL_SIZE from 4 to 30 caused database connection exhaustion or connection errors in checkout. |
| H3 | 0.00 | cause | networking | retired (Checkout is receiving the traffic and failing upstream calls…) | +0/−0 |  | Edge routing or WAF configuration is rejecting or failing requests to checkout. |

## Alternative explanations

- **H1**: Checkout DB_POOL_SIZE was patched shortly before the alert, but checkout workload metrics recorded zero db_errors_rps and logs show all failures are upstream dependency errors against inventory.
- **H3**: WAF rules and edge configuration modifications did not drop requests; edge passed requests through to checkout, which failed on dependency calls to inventory.

<details><summary>Evidence for/against other hypotheses</summary>

- H1 supports (moderate, O3/kubernetes): `"name": "checkout-config", "change": "modified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4…` — A configuration change directly on checkout's database pool size occurred less than 2 minutes before the high 5xx alert …
- H1 supports (moderate, O1/alertmanager): `"alertname": "ShopEdgeHigh5xxRate", "namespace": "shop", "service": "edge", "severity": "critical"},…` — Alert started firing at 11:25:14, immediately following the checkout deployment restart at 11:23:49.
- H1 contradicts (moderate, O8/prometheus): `no_data: ["db_errors_rps"]` — No database errors were recorded on checkout.
- H1 contradicts (strong, O5/kubernetes-logs): `upstream returned error upstream=inventory status=<n> body={"error":"stock lookup failed"}` — Checkout logs are dominated by inventory upstream failures rather than postgres/database connection errors.
- H4 supports (strong, O7/loki): `{"ts": "2026-10-13T11:31:10.682Z", "level": "error", "svc": "checkout", "version": "1.4.0", "msg": "…` — Inventory is explicitly returning HTTP 500 with 'stock lookup failed'.

</details>

## Uncertainty

- The underlying reason why inventory cannot reach its database (e.g., PostgreSQL service crash, connection saturation on the database server, or network/credential issues) requires inspecting the PostgreSQL database logs and pod status.
- 1 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Check PostgreSQL database pod status, logs, and connection limits in the shop namespace.
- Verify network connectivity, Service endpoint availability, and credentials from inventory pods to the PostgreSQL database.
- Ensure inventory retry and circuit-breaking logic gracefully degrades rather than causing cascading failure to checkout.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +3 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `active_alerts` {} — what is alerting and since when → O1
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: continue; evidence +4 accepted / 1 rejected; new hypotheses ['H4']
  - `pod_logs` {"namespace": "shop", "pod": "checkout-85d65646b7-c9kgd", "tail": 100} — Inspect recent logs of an active checkout pod to check connection pool errors. → O5
  - `find_traces` {"service": "checkout", "errors_only": true, "minutes": 15, "limit": 10} — Determine the origin of checkout errors: database query errors, internal exceptions, or downstream dependencies. → O6
  - `search_logs` {"namespace": "shop", "app": "checkout", "level": "error", "minutes": 15} — Check error messages logged by checkout since the rollout at 11:23:49. → O7
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — Check onset time of 5xx errors, DB errors, and dependency failures in checkout. → O8
  - posteriors: H1=0.01, H2=0.54, H3=0.03, H4=0.33, unexplained=0.09

**Round 2** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []; retired ['H1', 'H3']
  - `describe` {"kind": "deployment", "namespace": "shop", "name": "inventory"} — Inspect inventory configuration, env vars, mounted secrets/configmaps, and recent revisions → O9
  - `search_logs` {"namespace": "shop", "app": "inventory", "level": "error", "minutes": 15} — Find what internal error is causing inventory to return 'stock lookup failed' → O10
  - `workload_metrics` {"namespace": "shop", "workload": "inventory", "minutes": 30} — Check inventory golden signals, latency, DB errors, and dependency failures → O11
  - posteriors: H2=0.56, H4=0.34, unexplained=0.09

**Round 3** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H2=0.56, H4=0.34, unexplained=0.09

Stop reason: no new evidence for two rounds

</details>