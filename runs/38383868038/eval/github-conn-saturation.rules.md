# RCA: Capacity of edge was reduced (spec.replicas 4->2)

**Incident:** The checkout service is experiencing a sudden increase in 5xx errors.  
**Namespace:** `shop` · **Investigation:** `20261013-112520-b5ba2e` · **Reasoner:** `rules` · 3 rounds, 8 tool calls, 1.0s

## Root cause

Capacity of edge was reduced (spec.replicas 4->2)

*Hypothesis H2 · component `edge` · category `capacity`*

**Confidence: INCONCLUSIVE** (posterior 0.35). Inconclusive: no hypothesis is supported well enough to be called the root cause.

## Causal chain

1. 'timeout' observed: abels": {"dep": "checkout", "outcome": "timeout"}, "points": 104, "from": "2026- (O6)
2. 'timeout' observed: abels": {"dep": "checkout", "outcome": "timeout"}, "points": 104, "from": "2026- (O8)
3. 'timeout' observed: bels": {"dep": "inventory", "outcome": "timeout"}, "points": 79, "from": "2026-1 (O7)
4. 'timeout' observed: econds\": 5, \"successThreshold\": 1, \"timeoutSeconds\": 1}", "new": "{\"failur (O3)
5. 'timeout' observed: hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers) (O4)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O6 | prometheus | weak (+0.5) | `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 104, "from": "2026-10-13T10:55:36Z", "to": "20` | 'timeout' observed |
| ✅ O8 | prometheus | weak (+0.3) | `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 104, "from": "2026-10-13T10:55:36Z", "to": "20` | 'timeout' observed |
| ✅ O7 | prometheus | weak (+0.18) | `bels": {"dep": "inventory", "outcome": "timeout"}, "points": 79, "from": "2026-10-13T10:55:51Z", "to": "202` | 'timeout' observed |
| ✅ O3 | kubernetes | weak (+0.5) | `econds\": 5, \"successThreshold\": 1, \"timeoutSeconds\": 1}", "new": "{\"failureThreshold\": 3, \"httpGet\` | 'timeout' observed |
| ✅ O4 | kubernetes | weak (+0.3) | `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 16, "first_seen` | 'timeout' observed |

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
| 2026-10-13T11:02:21Z | onset | edge dependency_failures_rps on 2/3 series increase: 0.0 → 0.163444 | O6 |
| 2026-10-13T11:06:31Z | event | event Unhealthy x3 on Pod/checkout-69d8947794-29kkk,checkout-69d8947794-5qm4v: Liveness probe failed: Get "http://10.244.1.83:8080/healthz?deep=1": co… | O4 |
| 2026-10-13T11:06:35Z | event | event Unhealthy x11 on Pod/checkout-69d8947794-29kkk,checkout-69d8947794-5qm4v: Liveness probe failed: Get "http://10.244.1.83:8080/healthz?deep=1": d… | O4 |
| 2026-10-13T11:06:36Z | onset | edge errors_by_pod_rps[edge-7999f79dc7-km984] increase: 0.0 → 5.776859 | O6 |
| 2026-10-13T11:06:51Z | onset | edge error_ratio_5xx increase: 0.018764 → 1.0 | O6 |
| 2026-10-13T11:06:51Z | onset | checkout container_restarts on 3/3 series increase: 0.0 → 3.0 | O7 |
| 2026-10-13T11:07:09Z | event | event BackOff x3 on Pod/checkout-69d8947794-29kkk: Back-off restarting failed container checkout in pod checkout-69d8947794-29kkk_shop(1c3330… | O4 |
| 2026-10-13T11:07:09Z | event | event BackOff x3 on Pod/checkout-69d8947794-5qm4v: Back-off restarting failed container checkout in pod checkout-69d8947794-5qm4v_shop(8bb9a3… | O4 |
| 2026-10-13T11:07:11Z | event | event BackOff x3 on Pod/checkout-69d8947794-j8gmg: Back-off restarting failed container checkout in pod checkout-69d8947794-j8gmg_shop(615460… | O4 |
| 2026-10-13T11:10:06+00:00 | change | deployment/checkout modified: containers[checkout].livenessProbe {"failureThreshold": 1, "httpG… → {"failureThreshold": 3, "httpG… (by kubectl-client-… | O3 |
| 2026-10-13T11:10:06+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kube-controller-manager) | O3 |
| 2026-10-13T11:10:06+00:00 | change | deployment/edge modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-13T11:06:51Z — `2026-10-13T11:06:51Z` (O6, prometheus)
- edge error_ratio_5xx increase at 2026-10-13T11:06:51Z — `2026-10-13T11:06:51Z` (O8, prometheus)
- checkout error_ratio_5xx increase at 2026-10-13T11:24:36Z — `2026-10-13T11:24:36Z` (O7, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H2 | 0.35 | cause | capacity | active | +5/−0 | kubernetes, prometheus | Capacity of edge was reduced (spec.replicas 4->2) |
| H1 | 0.26 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service |
| H3 | 0.13 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap edge-waf-rules change (data.rules.json {"rules": [ {"id": "sqli-union-select", "pattern": "(?i)union\\s+select… |
| H4 | 0.10 | cause | probe_misconfiguration | active | +1/−0 | kubernetes | Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=… |

<details><summary>Evidence for/against other hypotheses</summary>

- H1 supports (moderate, O3/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"}], "actor": {"manager": …` — 'pool' observed near checkout-config
- H3 supports (weak, O3/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"}], "actor": {"manager": …` — 'pool' observed
- H1 supports (weak, O4/kubernetes): `\": dial tcp 10.244.1.25:8080: connect: connection refused", "count": 110, "first_seen": "2026-10-13…` — 'connection' observed
- H3 supports (weak, O4/kubernetes): `\": dial tcp 10.244.1.25:8080: connect: connection refused", "count": 110, "first_seen": "2026-10-13…` — 'connection' observed
- H4 supports (weak, O4/kubernetes): `ventory-8585795f99-wc2db"], "message": "Liveness probe failed: Get \"http://10.244.1.105:8080/health…` — 'liveness probe failed' observed

</details>

## Uncertainty

- Baseline rule reasoner: causal links are keyword-based, verify manually.

## Suggested remediation (not executed — the agent is read-only)

- Review and revert the implicated change if confirmed.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +0 accepted / 0 rejected; new hypotheses []
  - `active_alerts` {} — what is alerting and since when → O1
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: continue; evidence +10 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3', 'H4']
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O5
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O6
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H4 → O7
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — test H2 → O8
  - posteriors: H1=0.26, H2=0.35, H3=0.13, H4=0.10, unexplained=0.16

**Round 2** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.26, H2=0.35, H3=0.13, H4=0.10, unexplained=0.16

**Round 3** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.26, H2=0.35, H3=0.13, H4=0.10, unexplained=0.16

Stop reason: no new evidence for two rounds

</details>