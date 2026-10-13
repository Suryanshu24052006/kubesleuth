# RCA: Capacity of inventory was reduced (spec.replicas 4->1)

**Incident:** Checkout pods keep restarting and the storefront is throwing errors.  
**Namespace:** `shop` · **Investigation:** `20261013-110830-4c20ce` · **Reasoner:** `rules` · 3 rounds, 11 tool calls, 0.7s

## Root cause

Capacity of inventory was reduced (spec.replicas 4->1)

*Hypothesis H3 · component `inventory` · category `capacity`*

**Confidence: MEDIUM** (posterior 0.63). Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.

## Causal chain

1. 'timeout' observed: abels": {"dep": "checkout", "outcome": "timeout"}, "points": 58, "from": "2026-1 (O6)
2. 'timeout' observed near inventory: bels": {"dep": "inventory", "outcome": "timeout"}, "points": 62, "from": "2026-1 (O8)
3. 'timeout' observed near inventory: bels": {"dep": "inventory", "outcome": "timeout"}, "points": 62, "from": "2026-1 (O7)
4. 'timeout' observed: conds\": 10, \"successThreshold\": 1, \"timeoutSeconds\": 3}", "new": "{\"failur (O3)
5. 'timeout' observed near inventory: =1\": context deadline exceeded (Client.Timeout exceeded while awaiting headers) (O4)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O6 | prometheus | weak (+0.5) | `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 58, "from": "2026-10-13T10:40:01Z", "to": "202` | 'timeout' observed |
| ✅ O8 | prometheus | moderate (+0.72) | `bels": {"dep": "inventory", "outcome": "timeout"}, "points": 62, "from": "2026-10-13T10:40:01Z", "to": "202` | 'timeout' observed near inventory |
| ✅ O7 | prometheus | moderate (+0.432) | `bels": {"dep": "inventory", "outcome": "timeout"}, "points": 62, "from": "2026-10-13T10:40:01Z", "to": "202` | 'timeout' observed near inventory |
| ✅ O3 | kubernetes | weak (+0.5) | `conds\": 10, \"successThreshold\": 1, \"timeoutSeconds\": 3}", "new": "{\"failureThreshold\": 1, \"httpGet\` | 'timeout' observed |
| ✅ O4 | kubernetes | moderate (+0.72) | `=1\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 3, "first_seen"` | 'timeout' observed near inventory |
| ✅ O11 | prometheus | weak (+0.108) | `s_rps": [{"labels": {"kind": "ConnectionTimeout"}, "points": 29, "from": "2026-10-13T10:40:01Z", "to": "202` | 'timeout' observed |
| ✅ O9 | prometheus | weak (+0.065) | `"container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "dependency_failures_rps", "erro` | 'throttl' observed |
| ✅ O10 | prometheus | weak (+0.039) | `2\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "telemetry-collector-865ccb84` | 'throttl' observed |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x64 on Pod/inventory-6f6c46876d-2ccsv,inventory-6f6c46876d-6xqxs: Readiness probe failed: Get "http://10.244.1.48:8080/healthz": dial … | O4 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x19 on Pod/edge-555d7c4d58-d59d9,edge-555d7c4d58-g7bqs: Readiness probe failed: Get "http://10.244.1.50:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x88 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x22 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Readiness probe failed: Get "http://10.244.1.19:8080/hea… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x20 on Pod/recommendations-669dd5d8c4-4m4gp,recommendations-669dd5d8c4-rq57g: Readiness probe failed: Get "http://10.244.1.78:8080/hea… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-5sx5n,pricing-95c99775f-8drxw: Readiness probe failed: Get "http://10.244.1.26:8080/healthz": dial tcp 10.… | O4 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-ckttb: Readiness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:80… | O4 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-5jhhr,edge-6675f7688f-xnt2d: Liveness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1… | O4 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x5 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Liveness probe failed: Get "http://10.244.1.19:8080/healt… | O4 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Liveness probe failed: Get "http://10.244.1.25:8080/healthz": dial tcp … | O4 |
| 2026-10-13T10:39:04Z | event | event Unhealthy x1 on Pod/telemetry-collector-865ccb84c6-ckttb: Liveness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:808… | O4 |
| 2026-10-13T10:39:08Z | event | event FailedGetResourceMetric x1 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O4 |
| 2026-10-13T10:39:08Z | event | event FailedComputeMetricsReplicas x1 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T10:39:13Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O4 |
| 2026-10-13T10:43:01Z | onset | edge errors_by_pod_rps on 3/3 series increase: 0.0 → 0.022222 | O6 |
| 2026-10-13T10:43:01Z | onset | checkout errors_by_pod_rps[checkout-69cf4467b9-9p4zs] increase: 0.0 → 0.022222 | O7 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x2 on Pod/inventory-6f6c46876d-6xqxs,inventory-6f6c46876d-9v8h6: Failed to create pod sandbox: rpc error: code = Unavaila… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x2 on Pod/inventory-6ffc77fd45-6f8pt,inventory-6ffc77fd45-wc82r: error killing pod: [failed to "KillContainer" for "inventory" wit… | O4 |
| 2026-10-13T10:44:24Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc … | O4 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x1 on Pod/recommendations-67c55868cc-2mk82: Failed to create pod sandbox: rpc error: code = Unavailable desc = error read… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x1 on Pod/recommendations-7bd4dd95d6-ckzbg: error killing pod: [failed to "KillContainer" for "recommendations" with KillContainer… | O4 |
| 2026-10-13T10:44:25Z | event | event FailedKillPod x1 on Pod/edge-6675f7688f-xnt2d: error killing pod: [failed to "KillContainer" for "edge" with KillContainerError: "rpc err… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/inventory-6f6c46876d-9v8h6: Liveness probe failed: Get "http://10.244.1.53:8080/healthz": dial tcp 10.244.1.53:8080: c… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/recommendations-67c55868cc-2mk82: Liveness probe failed: Get "http://10.244.1.52:8080/healthz": dial tcp 10.244.1.52:8080: c… | O4 |
| 2026-10-13T10:47:45Z | change | service/telemetry-collector deleted | O3 |
| 2026-10-13T10:49:31Z | onset | inventory cpu_throttled_ratio[inventory-6f6c46876d-6xqxs] increase: 0.101399 → 0.286245 | O11 |
| 2026-10-13T10:51:01Z | onset | inventory latency_p95_seconds increase: 0.604145 → 1.49881 | O11 |
| 2026-10-13T10:52:16Z | onset | checkout error_ratio_5xx increase: 0.0 → 0.001182 | O7 |
| 2026-10-13T10:52:16Z | onset | checkout dependency_failures_rps on 2/3 series increase: 0.0 → 0.022222 | O7 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-13T10:52:31Z — `2026-10-13T10:52:31Z` (O6, prometheus)
- checkout error_ratio_5xx increase at 2026-10-13T10:52:16Z — `2026-10-13T10:52:16Z` (O8, prometheus)
- checkout error_ratio_5xx increase at 2026-10-13T10:52:16Z — `2026-10-13T10:52:16Z` (O7, prometheus)
- inventory error_ratio_5xx increase at 2026-10-13T11:07:01Z — `2026-10-13T11:07:01Z` (O11, prometheus)
- inventory db_errors_rps increase at 2026-10-13T11:07:01Z — `2026-10-13T11:07:01Z` (O11, prometheus)
- inventory db_errors_rps increase at 2026-10-13T11:07:01Z — `2026-10-13T11:07:01Z` (O11, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H3 | 0.63 | cause | capacity | active | +8/−0 | kubernetes, prometheus | Capacity of inventory was reduced (spec.replicas 4->1) |
| H1 | 0.10 | cause | dependency | active | +1/−0 | kubernetes | Service checkout has no healthy backends |
| H2 | 0.10 | cause | probe_misconfiguration | active | +1/−0 | kubernetes | Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 3, "httpGet": {"path": "/healthz", "po… |
| H4 | 0.05 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector-v2 was deleted () so callers cannot reach it |
| H5 | 0.05 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector was deleted () so callers cannot reach it |

<details><summary>Evidence for/against other hypotheses</summary>

- H1 supports (moderate, O4/kubernetes): `\": dial tcp 10.244.1.25:8080: connect: connection refused", "count": 88, "first_seen": "2026-10-13T…` — 'connection refused' observed near checkout
- H2 supports (moderate, O4/kubernetes): `heckout-69d8947794-j8gmg"], "message": "Liveness probe failed: Get \"http://10.244.1.83:8080/healthz…` — 'liveness probe failed' observed near checkout
- H4 supports (weak, O4/kubernetes): `\": dial tcp 10.244.1.25:8080: connect: connection refused", "count": 88, "first_seen": "2026-10-13T…` — 'connection refused' observed
- H5 supports (weak, O4/kubernetes): `\": dial tcp 10.244.1.25:8080: connect: connection refused", "count": 88, "first_seen": "2026-10-13T…` — 'connection refused' observed

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

**Round 1** — decision: continue; evidence +9 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3', 'H4', 'H5']
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O5
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O6
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H2 → O7
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H1 → O8
  - posteriors: H1=0.11, H2=0.11, H3=0.58, H4=0.05, H5=0.05, unexplained=0.09

**Round 2** — decision: continue; evidence +3 accepted / 0 rejected; new hypotheses []
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector-v2", "minutes": 30} — test H4 → O9
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector", "minutes": 30} — test H5 → O10
  - `workload_metrics` {"namespace": "shop", "workload": "inventory", "minutes": 30} — test H3 → O11
  - posteriors: H1=0.10, H2=0.10, H3=0.63, H4=0.05, H5=0.05, unexplained=0.08

**Round 3** — decision: model judged evidence sufficient; H3 p=0.63 (medium); evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.10, H2=0.10, H3=0.63, H4=0.05, H5=0.05, unexplained=0.08

Stop reason: model judged evidence sufficient; H3 p=0.63 (medium)

</details>