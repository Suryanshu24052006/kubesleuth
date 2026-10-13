# RCA: Capacity of inventory was reduced (spec.replicas 4->1)

**Incident:** The edge service latency and error rate spiked; customers report timeouts.  
**Namespace:** `shop` · **Investigation:** `20261013-111524-0faf0b` · **Reasoner:** `rules` · 2 rounds, 8 tool calls, 1.7s

## Root cause

Capacity of inventory was reduced (spec.replicas 4->1)

*Hypothesis H3 · component `inventory` · category `capacity`*

**Confidence: MEDIUM** (posterior 0.56). Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.

## Causal chain

1. 'timeout' observed: abels": {"dep": "checkout", "outcome": "timeout"}, "points": 65, "from": "2026-1 (O7)
2. 'timeout' observed near inventory: bels": {"dep": "inventory", "outcome": "timeout"}, "points": 44, "from": "2026-1 (O5)
3. 'timeout' observed: s_rps": [{"labels": {"kind": "ConnectionTimeout"}, "points": 17, "from": "2026-1 (O6)
4. 'timeout' observed: econds\": 5, \"successThreshold\": 1, \"timeoutSeconds\": 1}", "new": "{\"failur (O3)
5. 'timeout' observed: hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers) (O4)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O7 | prometheus | weak (+0.5) | `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 65, "from": "2026-10-13T10:55:41Z", "to": "202` | 'timeout' observed |
| ✅ O5 | prometheus | moderate (+0.72) | `bels": {"dep": "inventory", "outcome": "timeout"}, "points": 44, "from": "2026-10-13T10:55:41Z", "to": "202` | 'timeout' observed near inventory |
| ✅ O6 | prometheus | weak (+0.18) | `s_rps": [{"labels": {"kind": "ConnectionTimeout"}, "points": 17, "from": "2026-10-13T11:06:56Z", "to": "202` | 'timeout' observed |
| ✅ O3 | kubernetes | weak (+0.5) | `econds\": 5, \"successThreshold\": 1, \"timeoutSeconds\": 1}", "new": "{\"failureThreshold\": 3, \"httpGet\` | 'timeout' observed |
| ✅ O4 | kubernetes | weak (+0.3) | `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 20, "first_seen` | 'timeout' observed |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x33 on Pod/edge-555d7c4d58-d59d9,edge-555d7c4d58-g7bqs: Readiness probe failed: Get "http://10.244.1.50:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x71 on Pod/inventory-6f6c46876d-2ccsv,inventory-6f6c46876d-6xqxs: Readiness probe failed: Get "http://10.244.1.48:8080/healthz": dial … | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x24 on Pod/recommendations-55b5fd5477-6lbkr,recommendations-55b5fd5477-cdtzd: Readiness probe failed: Get "http://10.244.1.88:8080/hea… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x97 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x22 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Readiness probe failed: Get "http://10.244.1.19:8080/hea… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-5sx5n,pricing-95c99775f-8drxw: Readiness probe failed: Get "http://10.244.1.26:8080/healthz": dial tcp 10.… | O4 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/edge-6675f7688f-5jhhr,edge-6675f7688f-xnt2d: Liveness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1… | O4 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-ckttb: Readiness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:80… | O4 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x5 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Liveness probe failed: Get "http://10.244.1.19:8080/healt… | O4 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Liveness probe failed: Get "http://10.244.1.25:8080/healthz": dial tcp … | O4 |
| 2026-10-13T10:39:04Z | event | event Unhealthy x1 on Pod/telemetry-collector-865ccb84c6-ckttb: Liveness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:808… | O4 |
| 2026-10-13T10:39:08Z | event | event FailedGetResourceMetric x1 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O4 |
| 2026-10-13T10:39:08Z | event | event FailedComputeMetricsReplicas x1 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T10:39:13Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O4 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x2 on Pod/inventory-6f6c46876d-6xqxs,inventory-6f6c46876d-9v8h6: Failed to create pod sandbox: rpc error: code = Unavaila… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x2 on Pod/inventory-6ffc77fd45-6f8pt,inventory-6ffc77fd45-wc82r: error killing pod: [failed to "KillContainer" for "inventory" wit… | O4 |
| 2026-10-13T10:44:24Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc … | O4 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x1 on Pod/recommendations-67c55868cc-2mk82: Failed to create pod sandbox: rpc error: code = Unavailable desc = error read… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x1 on Pod/recommendations-7bd4dd95d6-ckzbg: error killing pod: [failed to "KillContainer" for "recommendations" with KillContainer… | O4 |
| 2026-10-13T10:44:25Z | event | event FailedKillPod x1 on Pod/edge-6675f7688f-xnt2d: error killing pod: [failed to "KillContainer" for "edge" with KillContainerError: "rpc err… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/inventory-6f6c46876d-9v8h6: Liveness probe failed: Get "http://10.244.1.53:8080/healthz": dial tcp 10.244.1.53:8080: c… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/recommendations-67c55868cc-2mk82: Liveness probe failed: Get "http://10.244.1.52:8080/healthz": dial tcp 10.244.1.52:8080: c… | O4 |
| 2026-10-13T10:49:26Z | onset | inventory cpu_throttled_ratio[inventory-6f6c46876d-6xqxs] increase: 0.099069 → 0.292308 | O6 |
| 2026-10-13T10:52:26Z | onset | checkout errors_by_pod_rps[checkout-9fc96469d-7h92b] increase: 0.0 → 0.022222 | O5 |
| 2026-10-13T10:52:26Z | onset | edge errors_by_pod_rps on 3/3 series increase: 0.0 → 0.022222 | O7 |
| 2026-10-13T10:55:11Z | onset | edge dependency_failures_rps on 3/3 series increase: 0.0 → 0.028772 | O7 |
| 2026-10-13T10:55:18+00:00 | change | deployment/inventory modified: spec.replicas 4 → 1 (by kube-controller-manager) | O3 |
| 2026-10-13T10:55:24Z | event | event FailedGetResourceMetric x4 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods might… | O4 |
| 2026-10-13T10:55:24Z | event | event FailedComputeMetricsReplicas x4 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-13T10:55:26Z — `2026-10-13T10:55:26Z` (O7, prometheus)
- checkout error_ratio_5xx increase at 2026-10-13T10:57:11Z — `2026-10-13T10:57:11Z` (O5, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H3 | 0.56 | cause | capacity | active | +5/−0 | kubernetes, prometheus | Capacity of inventory was reduced (spec.replicas 4->1) |
| H1 | 0.17 | cause | configuration | active | +2/−0 | kubernetes, prometheus | ConfigMap edge-waf-rules change (data.rules.json {"rules": [ {"id": "sqli-union-select", "pattern": "(?i)union\\s+select… |
| H2 | 0.10 | cause | probe_misconfiguration | active | +1/−0 | kubernetes | Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=… |

<details><summary>Evidence for/against other hypotheses</summary>

- H1 supports (weak, O6/prometheus): `"db_errors_rps": [{"labels": {"kind": "ConnectionTimeout"}, "points": 17, "from": "2026-10-13T11:06:…` — 'connection' observed
- H1 supports (weak, O4/kubernetes): `\": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 33, "first_seen": "2026-10-13T…` — 'connection' observed
- H2 supports (weak, O4/kubernetes): `", "edge-f647cd7c4-mklgr"], "message": "Liveness probe failed: Get \"http://10.244.1.98:8080/healthz…` — 'liveness probe failed' observed

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

**Round 1** — decision: continue; evidence +8 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H2 → O5
  - `workload_metrics` {"namespace": "shop", "workload": "inventory", "minutes": 30} — test H3 → O6
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O7
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O8
  - posteriors: H1=0.17, H2=0.10, H3=0.56, unexplained=0.17

**Round 2** — decision: model judged evidence sufficient; H3 p=0.56 (medium); evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.17, H2=0.10, H3=0.56, unexplained=0.17

Stop reason: model judged evidence sufficient; H3 p=0.56 (medium)

</details>