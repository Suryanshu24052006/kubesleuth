# RCA: Capacity of inventory was reduced (spec.replicas 4->1)

**Incident:** Checkout requests are timing out and the edge is returning 5xx.  
**Namespace:** `shop` · **Investigation:** `20261013-105949-8239ff` · **Reasoner:** `rules` · 4 rounds, 10 tool calls, 0.6s

## Root cause

Capacity of inventory was reduced (spec.replicas 4->1)

*Hypothesis H1 · component `inventory` · category `capacity`*

**Confidence: LOW** (posterior 0.41). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. 'timeout' observed: abels": {"dep": "checkout", "outcome": "timeout"}, "points": 38, "from": "2026-1 (O8)
2. 'timeout' observed: s_rps": [{"labels": {"kind": "ConnectionTimeout"}, "points": 22, "from": "2026-1 (O7)
3. 'throttl' observed: "container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "depe (O5)
4. 'timeout' observed near inventory: hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers) (O2)
5. 'throttl' observed: 1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "t (O9)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O8 | prometheus | weak (+0.5) | `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 38, "from": "2026-10-13T10:40:04Z", "to": "202` | 'timeout' observed |
| ✅ O7 | prometheus | weak (+0.3) | `s_rps": [{"labels": {"kind": "ConnectionTimeout"}, "points": 22, "from": "2026-10-13T10:40:04Z", "to": "202` | 'timeout' observed |
| ✅ O5 | prometheus | weak (+0.18) | `"container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "dependency_failures_rps", "erro` | 'throttl' observed |
| ✅ O2 | kubernetes | moderate (+1.2) | `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 11, "first_seen` | 'timeout' observed near inventory |
| ✅ O9 | prometheus | weak (+0.108) | `1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "telemetry-collector-865ccb84` | 'throttl' observed |
| ✅ O10 | prometheus | weak (+0.065) | `1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "catalog-indexer-6f6b545fdb-4` | 'throttl' observed |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:38:53+00:00 | change | rollout/telemetry-collector new-revision | O3 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x41 on Pod/inventory-6f6c46876d-2ccsv,inventory-6f6c46876d-6xqxs: Readiness probe failed: Get "http://10.244.1.48:8080/healthz": dial … | O2 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x13 on Pod/edge-555d7c4d58-d59d9,edge-555d7c4d58-g7bqs: Readiness probe failed: Get "http://10.244.1.50:8080/healthz": dial tcp 10.244… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x13 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-mtscn: Readiness probe failed: Get "http://10.244.1.19:8080/hea… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x16 on Pod/recommendations-67c55868cc-2mk82,recommendations-67c55868cc-5f6w2: Readiness probe failed: Get "http://10.244.1.52:8080/hea… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x29 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-5sx5n,pricing-95c99775f-8drxw: Readiness probe failed: Get "http://10.244.1.26:8080/healthz": dial tcp 10.… | O2 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-ckttb: Readiness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:80… | O2 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-5jhhr,edge-6675f7688f-xnt2d: Liveness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1… | O2 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x3 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-mtscn: Liveness probe failed: Get "http://10.244.1.19:8080/healt… | O2 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Liveness probe failed: Get "http://10.244.1.25:8080/healthz": dial tcp … | O2 |
| 2026-10-13T10:39:04Z | event | event Unhealthy x1 on Pod/telemetry-collector-865ccb84c6-ckttb: Liveness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:808… | O2 |
| 2026-10-13T10:39:08Z | event | event FailedGetResourceMetric x1 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O2 |
| 2026-10-13T10:39:08Z | event | event FailedComputeMetricsReplicas x1 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O2 |
| 2026-10-13T10:39:09+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (by kube-controller-manager) | O3 |
| 2026-10-13T10:39:13Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O2 |
| 2026-10-13T10:39:19+00:00 | change | statefulset/postgres last-write (by kube-controller-manager) | O3 |
| 2026-10-13T10:42:49Z | onset | edge errors_by_pod_rps on 3/3 series increase: 0.0 → 0.022222 | O8 |
| 2026-10-13T10:44:11+00:00 | change | deployment/checkout modified: template.annotations null → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |
| 2026-10-13T10:44:11+00:00 | change | deployment/edge modified: template.annotations null → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |
| 2026-10-13T10:44:11+00:00 | change | deployment/recommendations modified: template.annotations null → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |
| 2026-10-13T10:44:11+00:00 | change | deployment/inventory modified: template.annotations null → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |
| 2026-10-13T10:44:11+00:00 | change | rollout/checkout new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O3 |
| 2026-10-13T10:44:11+00:00 | change | rollout/edge new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O3 |
| 2026-10-13T10:44:11+00:00 | change | rollout/inventory new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O3 |
| 2026-10-13T10:44:11+00:00 | change | rollout/recommendations new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O3 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x2 on Pod/inventory-6f6c46876d-6xqxs,inventory-6f6c46876d-9v8h6: Failed to create pod sandbox: rpc error: code = Unavaila… | O2 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x2 on Pod/inventory-6ffc77fd45-6f8pt,inventory-6ffc77fd45-wc82r: error killing pod: [failed to "KillContainer" for "inventory" wit… | O2 |
| 2026-10-13T10:44:24Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc … | O2 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-13T10:46:49Z — `2026-10-13T10:46:49Z` (O8, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.41 | cause | capacity | active | +6/−0 | kubernetes, prometheus | Capacity of inventory was reduced (spec.replicas 4->1) |
| H4 | 0.22 | cause | capacity | active | +6/−0 | kubernetes, prometheus | Capacity of catalog-indexer was reduced (spec.replicas 3->1) |
| H5 | 0.13 | cause | dependency | active | +1/−0 | kubernetes | Service inventory has no healthy backends |
| H2 | 0.06 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector-v2 was deleted () so callers cannot reach it |
| H3 | 0.06 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector was deleted () so callers cannot reach it |

<details><summary>Evidence for/against other hypotheses</summary>

- H4 supports (weak, O8/prometheus): `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 38, "from": "2026-10-13T10:40:04Z", "to…` — 'timeout' observed
- H4 supports (weak, O7/prometheus): `s_rps": [{"labels": {"kind": "ConnectionTimeout"}, "points": 22, "from": "2026-10-13T10:40:04Z", "to…` — 'timeout' observed
- H4 supports (weak, O5/prometheus): `"container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "dependency_failures_rps"…` — 'throttl' observed
- H2 supports (weak, O2/kubernetes): `\": dial tcp 10.244.1.48:8080: connect: connection refused", "count": 41, "first_seen": "2026-10-13T…` — 'connection refused' observed
- H3 supports (weak, O2/kubernetes): `\": dial tcp 10.244.1.48:8080: connect: connection refused", "count": 41, "first_seen": "2026-10-13T…` — 'connection refused' observed
- H4 supports (weak, O2/kubernetes): `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 11, "fir…` — 'timeout' observed
- H5 supports (moderate, O2/kubernetes): `\": dial tcp 10.244.1.48:8080: connect: connection refused", "count": 41, "first_seen": "2026-10-13T…` — 'connection refused' observed near inventory
- H4 supports (weak, O9/prometheus): `1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "telemetry-collector-8…` — 'throttl' observed
- H4 supports (moderate, O10/prometheus): `1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "catalog-indexer-6f6b5…` — 'throttl' observed near catalog-indexer

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
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: continue; evidence +11 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3', 'H4', 'H5']
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector-v2", "minutes": 30} — test H2 → O5
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O6
  - `workload_metrics` {"namespace": "shop", "workload": "inventory", "minutes": 30} — test H1 → O7
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O8
  - posteriors: H1=0.39, H2=0.07, H3=0.07, H4=0.20, H5=0.15, unexplained=0.12

**Round 2** — decision: continue; evidence +4 accepted / 0 rejected; new hypotheses []
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector", "minutes": 30} — test H3 → O9
  - `workload_metrics` {"namespace": "shop", "workload": "catalog-indexer", "minutes": 30} — test H4 → O10
  - posteriors: H1=0.41, H2=0.06, H3=0.06, H4=0.22, H5=0.13, unexplained=0.11

**Round 3** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.41, H2=0.06, H3=0.06, H4=0.22, H5=0.13, unexplained=0.11

**Round 4** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.41, H2=0.06, H3=0.06, H4=0.22, H5=0.13, unexplained=0.11

Stop reason: no new evidence for two rounds

</details>