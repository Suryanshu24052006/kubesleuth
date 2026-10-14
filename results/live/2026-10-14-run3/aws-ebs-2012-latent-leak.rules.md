# RCA: Service telemetry-collector was deleted () so callers cannot reach it

**Incident:** Checkout is intermittently failing with 502s; recommendations pods are restarting.  
**Namespace:** `shop` · **Investigation:** `20261014-080457-52822c` · **Reasoner:** `rules` · 3 rounds, 7 tool calls, 0.3s

## Root cause

Service telemetry-collector was deleted () so callers cannot reach it

*Hypothesis H1 · component `telemetry-collector` · category `dependency`*

**Confidence: LOW** (posterior 0.38). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. 'connection refused' observed: \": dial tcp 10.244.1.25:8080: connect: connection refused", "count": 12, "first (O2)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O2 | kubernetes | weak (+0.5) | `\": dial tcp 10.244.1.25:8080: connect: connection refused", "count": 12, "first_seen": "2026-10-14T07:53:33Z"…` | 'connection refused' observed |

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
| 2026-10-14T07:53:30+00:00 | change | deployment/catalog-indexer last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/checkout last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/edge last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/inventory last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/loadgen last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/review-bot last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/telemetry-collector last-write (by kubectl-client-side-apply) | O3 |

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.38 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector was deleted () so callers cannot reach it |

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

**Round 1** — decision: continue; evidence +1 accepted / 0 rejected; new hypotheses ['H1']
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector", "minutes": 30} — test H1 → O5
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O6
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O7
  - posteriors: H1=0.38, unexplained=0.62

**Round 2** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.38, unexplained=0.62

**Round 3** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.38, unexplained=0.62

Stop reason: no new evidence for two rounds

</details>