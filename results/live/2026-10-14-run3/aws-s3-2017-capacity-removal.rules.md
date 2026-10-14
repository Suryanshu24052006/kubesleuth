# RCA: Capacity of inventory was reduced (spec.replicas 4->1)

**Incident:** Checkout requests are timing out and the edge is returning 5xx.  
**Namespace:** `shop` · **Investigation:** `20261014-081659-4a2d6a` · **Reasoner:** `rules` · 3 rounds, 9 tool calls, 0.3s

## Root cause

Capacity of inventory was reduced (spec.replicas 4->1)

*Hypothesis H3 · component `inventory` · category `capacity`*

**Confidence: MEDIUM** (posterior 0.72). Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.

## Causal chain

1. 'throttl' observed: "container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "depe (O5)
2. 'throttl' observed: "container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "depe (O7)
3. 'throttl' observed: 1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "c (O6)
4. 'throttl' observed near inventory: ration in PagerDuty.\n"}, {"alert": "CPUThrottlingHigh", "severity": "info", "st (O1)
5. 'timeout' observed near inventory: hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers) (O2)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O5 | prometheus | weak (+0.5) | `"container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "dependency_failures_rps", "erro` | 'throttl' observed |
| ✅ O7 | prometheus | weak (+0.3) | `"container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "dependency_failures_rps", "erro` | 'throttl' observed |
| ✅ O6 | prometheus | weak (+0.18) | `1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "catalog-indexer-6f6b545fdb-7` | 'throttl' observed |
| ✅ O1 | alertmanager | moderate (+1.2) | `ration in PagerDuty.\n"}, {"alert": "CPUThrottlingHigh", "severity": "info", "state": "active", "starts_at"` | 'throttl' observed near inventory |
| ✅ O2 | kubernetes | moderate (+1.2) | `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 11, "first_seen` | 'timeout' observed near inventory |
| ✅ O9 | prometheus | moderate (+0.259) | `8\u2588\u2587", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "inventory-6ffc77fd45-28b67"}` | 'throttl' observed near inventory |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-14T07:49:52.298Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-14T07:53:29+00:00 | change | configmap/checkout-config last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:29+00:00 | change | configmap/edge-waf-rules last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:29+00:00 | change | configmap/feature-flags last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:29+00:00 | change | configmap/kube-root-ca.crt last-write (by kube-controller-manager) | O4 |
| 2026-10-14T07:53:29+00:00 | change | service/catalog-indexer last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:29+00:00 | change | service/checkout last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:29+00:00 | change | service/edge last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:29+00:00 | change | service/inventory last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:29+00:00 | change | service/postgres last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:29+00:00 | change | service/pricing last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | deployment/inventory modified: spec.replicas 4 → 1 (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | rollout/catalog-indexer new-revision | O4 |
| 2026-10-14T07:53:30+00:00 | change | rollout/checkout new-revision | O4 |
| 2026-10-14T07:53:30+00:00 | change | rollout/edge new-revision | O4 |
| 2026-10-14T07:53:30+00:00 | change | rollout/inventory new-revision | O4 |
| 2026-10-14T07:53:30+00:00 | change | rollout/loadgen new-revision | O4 |
| 2026-10-14T07:53:30+00:00 | change | rollout/pricing new-revision | O4 |
| 2026-10-14T07:53:30+00:00 | change | rollout/recommendations new-revision | O4 |
| 2026-10-14T07:53:30+00:00 | change | rollout/review-bot new-revision | O4 |
| 2026-10-14T07:53:30+00:00 | change | rollout/telemetry-collector new-revision | O4 |
| 2026-10-14T07:53:30+00:00 | change | service/recommendations last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | deployment/checkout last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | deployment/edge last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | deployment/loadgen last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | deployment/pricing last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | deployment/recommendations last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | deployment/review-bot last-write (by kubectl-client-side-apply) | O4 |
| 2026-10-14T07:53:30+00:00 | change | deployment/telemetry-collector last-write (by kubectl-client-side-apply) | O4 |

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H3 | 0.72 | cause | capacity | active | +6/−0 | alertmanager, kubernetes, prometheus | Capacity of inventory was reduced (spec.replicas 4->1) |
| H2 | 0.20 | cause | capacity | active | +6/−0 | alertmanager, kubernetes, prometheus | Capacity of catalog-indexer was reduced (spec.replicas 3->1) |
| H1 | 0.03 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector-v2 was deleted () so callers cannot reach it |

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (weak, O5/prometheus): `"container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "dependency_failures_rps"…` — 'throttl' observed
- H2 supports (weak, O7/prometheus): `"container_restarts", "cpu_cores", "cpu_throttled_ratio", "db_errors_rps", "dependency_failures_rps"…` — 'throttl' observed
- H2 supports (moderate, O6/prometheus): `1\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "catalog-indexer-6f6b5…` — 'throttl' observed near catalog-indexer
- H2 supports (weak, O1/alertmanager): `ration in PagerDuty.\n"}, {"alert": "CPUThrottlingHigh", "severity": "info", "state": "active", "sta…` — 'throttl' observed
- H1 supports (weak, O2/kubernetes): `\": dial tcp 10.244.1.27:8080: connect: connection refused", "count": 17, "first_seen": "2026-10-14T…` — 'connection refused' observed
- H2 supports (weak, O2/kubernetes): `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 11, "fir…` — 'timeout' observed
- H2 supports (weak, O9/prometheus): `8\u2588\u2587", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "inventory-6ffc77fd45-…` — 'throttl' observed

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

**Round 1** — decision: continue; evidence +11 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `workload_metrics` {"namespace": "shop", "workload": "kps-kubelet", "minutes": 30} — symptom onset → O5
  - `workload_metrics` {"namespace": "shop", "workload": "catalog-indexer", "minutes": 30} — test H2 → O6
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector-v2", "minutes": 30} — test H1 → O7
  - `find_traces` {"service": "kps-kubelet", "minutes": 15} — where do errors originate? → O8
  - posteriors: H1=0.04, H2=0.22, H3=0.68, unexplained=0.06

**Round 2** — decision: continue; evidence +2 accepted / 0 rejected; new hypotheses []
  - `workload_metrics` {"namespace": "shop", "workload": "inventory", "minutes": 30} — test H3 → O9
  - posteriors: H1=0.03, H2=0.20, H3=0.72, unexplained=0.05

**Round 3** — decision: model judged evidence sufficient; H3 p=0.72 (medium); evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.03, H2=0.20, H3=0.72, unexplained=0.05

Stop reason: model judged evidence sufficient; H3 p=0.72 (medium)

</details>