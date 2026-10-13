# RCA: Capacity of inventory was reduced (spec.replicas 4->1)

**Incident:** Checkout requests are timing out and the edge is returning 5xx.  
**Namespace:** `shop` · **Investigation:** `20261013-124723-6f1ae1` · **Reasoner:** `rules` · 3 rounds, 9 tool calls, 0.7s

## Root cause

Capacity of inventory was reduced (spec.replicas 4->1)

*Hypothesis H1 · component `inventory` · category `capacity`*

**Confidence: MEDIUM** (posterior 0.60). Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.

## Causal chain

1. 'timeout' observed: abels": {"dep": "checkout", "outcome": "timeout"}, "points": 87, "from": "2026-1 (O6)
2. 'throttl' observed near inventory: 8\u2587\u2585", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "i (O7)
3. 'throttl' observed: "container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "depe (O5)
4. 'timeout' observed near inventory: hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers) (O2)
5. 'throttl' observed: 1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "c (O9)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O6 | prometheus | weak (+0.5) | `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 87, "from": "2026-10-13T12:22:53Z", "to": "202` | 'timeout' observed |
| ✅ O7 | prometheus | moderate (+0.72) | `8\u2587\u2585", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "inventory-668745bb49-5xmp9"}` | 'throttl' observed near inventory |
| ✅ O5 | prometheus | weak (+0.18) | `"container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "dependency_failures_rps", "erro` | 'throttl' observed |
| ✅ O2 | kubernetes | moderate (+1.2) | `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 9, "first_seen"` | 'timeout' observed near inventory |
| ✅ O9 | prometheus | weak (+0.108) | `1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "catalog-indexer-6f6b545fdb-f` | 'throttl' observed |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T12:17:30.161Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T12:21:13+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (by kubectl-client-side-apply) | O4 |
| 2026-10-13T12:21:13+00:00 | change | rollout/catalog-indexer new-revision | O4 |
| 2026-10-13T12:21:13+00:00 | change | rollout/checkout new-revision | O4 |
| 2026-10-13T12:21:13+00:00 | change | rollout/edge new-revision | O4 |
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
| 2026-10-13T12:26:21+00:00 | change | deployment/checkout modified: template.annotations null → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O4 |
| 2026-10-13T12:26:21+00:00 | change | deployment/edge modified: template.annotations null → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O4 |
| 2026-10-13T12:26:21+00:00 | change | deployment/recommendations modified: template.annotations null → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O4 |
| 2026-10-13T12:26:21+00:00 | change | deployment/inventory modified: template.annotations null → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O4 |
| 2026-10-13T12:26:21+00:00 | change | rollout/checkout new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T12:26:21+00:00 | change | rollout/edge new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T12:26:21+00:00 | change | rollout/inventory new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T12:26:21+00:00 | change | rollout/recommendations new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T12:26:23Z | event | event FailedKillPod x1 on Pod/checkout-69cf4467b9-k5j84: error killing pod: [failed to "KillContainer" for "checkout" with KillContainerError: "rpc… | O2 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x2 on Pod/checkout-8457f655f7-jwzw6,checkout-8457f655f7-nmx9x: Failed to create pod sandbox: rpc error: code = Unavailabl… | O2 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-13T12:46:08Z — `2026-10-13T12:46:08Z` (O6, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.60 | cause | capacity | active | +5/−0 | kubernetes, prometheus | Capacity of inventory was reduced (spec.replicas 4->1) |
| H3 | 0.23 | cause | capacity | active | +5/−0 | kubernetes, prometheus | Capacity of catalog-indexer was reduced (spec.replicas 3->1) |
| H2 | 0.07 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector-v2 was deleted () so callers cannot reach it |

<details><summary>Evidence for/against other hypotheses</summary>

- H3 supports (weak, O6/prometheus): `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 87, "from": "2026-10-13T12:22:53Z", "to…` — 'timeout' observed
- H3 supports (weak, O7/prometheus): `8\u2587\u2585", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "inventory-668745bb49-…` — 'throttl' observed
- H3 supports (weak, O5/prometheus): `"container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "dependency_failures_rps"…` — 'throttl' observed
- H2 supports (weak, O2/kubernetes): `\": dial tcp 10.244.1.53:8080: connect: connection refused", "count": 37, "first_seen": "2026-10-13T…` — 'connection refused' observed
- H3 supports (weak, O2/kubernetes): `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 9, "firs…` — 'timeout' observed
- H3 supports (moderate, O9/prometheus): `1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "catalog-indexer-6f6b5…` — 'throttl' observed near catalog-indexer

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
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O3
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O4

**Round 1** — decision: continue; evidence +9 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector-v2", "minutes": 30} — test H2 → O5
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O6
  - `workload_metrics` {"namespace": "shop", "workload": "inventory", "minutes": 30} — test H1 → O7
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O8
  - posteriors: H1=0.61, H2=0.07, H3=0.20, unexplained=0.12

**Round 2** — decision: continue; evidence +2 accepted / 0 rejected; new hypotheses []
  - `workload_metrics` {"namespace": "shop", "workload": "catalog-indexer", "minutes": 30} — test H3 → O9
  - posteriors: H1=0.60, H2=0.07, H3=0.23, unexplained=0.11

**Round 3** — decision: model judged evidence sufficient; H1 p=0.60 (medium); evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.60, H2=0.07, H3=0.23, unexplained=0.11

Stop reason: model judged evidence sufficient; H1 p=0.60 (medium)

</details>