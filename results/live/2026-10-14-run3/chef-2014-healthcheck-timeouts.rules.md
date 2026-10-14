# RCA: Service checkout has no healthy backends

**Incident:** Checkout pods keep restarting and the storefront is throwing errors.  
**Namespace:** `shop` · **Investigation:** `20261014-082516-476efd` · **Reasoner:** `rules` · 3 rounds, 9 tool calls, 0.3s

## Root cause

Service checkout has no healthy backends

*Hypothesis H1 · component `checkout` · category `dependency`*

**Confidence: INCONCLUSIVE** (posterior 0.30). Inconclusive: no hypothesis is supported well enough to be called the root cause.

## Causal chain

1. 'connection refused' observed near checkout: \": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 65, "first (O4)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O4 | kubernetes | moderate (+1.2) | `\": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 65, "first_seen": "2026-10-14T07:53:33Z"…` | 'connection refused' observed near checkout |

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
| 2026-10-14T07:53:30+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (since reverted) (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/inventory modified: spec.replicas 4 → 1 (since reverted) (by kubectl-client-side-apply) | O3 |
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
| 2026-10-14T07:53:30+00:00 | change | deployment/edge last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/loadgen last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/review-bot last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/telemetry-collector last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | statefulset/postgres last-write (by kubectl-client-side-apply) | O3 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-14T08:13:32Z — `2026-10-14T08:13:32Z` (O7, prometheus)
- checkout error_ratio_5xx increase at 2026-10-14T08:13:47Z — `2026-10-14T08:13:47Z` (O5, prometheus)
- checkout error_ratio_5xx increase at 2026-10-14T08:13:47Z — `2026-10-14T08:13:47Z` (O8, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.30 | cause | dependency | active | +1/−0 | kubernetes | Service checkout has no healthy backends |
| H2 | 0.30 | cause | probe_misconfiguration | active | +1/−0 | kubernetes | Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 3, "httpGet": {"path": "/healthz", "po… |
| H3 | 0.15 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector-v2 was deleted () so callers cannot reach it |

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (moderate, O4/kubernetes): `heckout-68fb58bcfd-jsmz4"], "message": "Liveness probe failed: Get \"http://10.244.1.50:8080/healthz…` — 'liveness probe failed' observed near checkout
- H3 supports (weak, O4/kubernetes): `\": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 65, "first_seen": "2026-10-14T…` — 'connection refused' observed

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

**Round 1** — decision: continue; evidence +3 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H1 → O5
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O6
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O7
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H2 → O8
  - posteriors: H1=0.30, H2=0.30, H3=0.15, unexplained=0.25

**Round 2** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector-v2", "minutes": 30} — test H3 → O9
  - posteriors: H1=0.30, H2=0.30, H3=0.15, unexplained=0.25

**Round 3** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.30, H2=0.30, H3=0.15, unexplained=0.25

Stop reason: no new evidence for two rounds

</details>