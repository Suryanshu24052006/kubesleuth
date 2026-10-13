# RCA: Service telemetry-collector was deleted () so callers cannot reach it

**Incident:** Checkout is intermittently failing with 502s; recommendations pods are restarting.  
**Namespace:** `shop` · **Investigation:** `20261013-105119-f0caeb` · **Reasoner:** `rules` · 3 rounds, 7 tool calls, 0.5s

## Root cause

Service telemetry-collector was deleted () so callers cannot reach it

*Hypothesis H1 · component `telemetry-collector` · category `dependency`*

**Confidence: LOW** (posterior 0.38). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. 'connection refused' observed: \": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 9, "first_ (O2)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O2 | kubernetes | weak (+0.5) | `\": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 9, "first_seen": "2026-10-13T10:38:56Z",…` | 'connection refused' observed |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:38:50+00:00 | change | configmap/checkout-config last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:50+00:00 | change | configmap/edge-waf-rules last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:50+00:00 | change | configmap/feature-flags last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:50+00:00 | change | configmap/kube-root-ca.crt last-write (by kube-controller-manager) | O3 |
| 2026-10-13T10:38:50+00:00 | change | service/catalog-indexer last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:51+00:00 | change | service/checkout last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:51+00:00 | change | service/edge last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:51+00:00 | change | service/inventory last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:51+00:00 | change | service/postgres last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:52+00:00 | change | rollout/catalog-indexer new-revision | O3 |
| 2026-10-13T10:38:52+00:00 | change | rollout/checkout new-revision | O3 |
| 2026-10-13T10:38:52+00:00 | change | rollout/edge new-revision | O3 |
| 2026-10-13T10:38:52+00:00 | change | rollout/inventory new-revision | O3 |
| 2026-10-13T10:38:52+00:00 | change | rollout/loadgen new-revision | O3 |
| 2026-10-13T10:38:52+00:00 | change | rollout/pricing new-revision | O3 |
| 2026-10-13T10:38:52+00:00 | change | rollout/recommendations new-revision | O3 |
| 2026-10-13T10:38:52+00:00 | change | rollout/review-bot new-revision | O3 |
| 2026-10-13T10:38:52+00:00 | change | service/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:52+00:00 | change | service/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:38:53+00:00 | change | rollout/telemetry-collector new-revision | O3 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x9 on Pod/edge-555d7c4d58-d59d9,edge-555d7c4d58-g7bqs: Readiness probe failed: Get "http://10.244.1.50:8080/healthz": dial tcp 10.244.… | O2 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x22 on Pod/inventory-6f6c46876d-2ccsv,inventory-6f6c46876d-6xqxs: Readiness probe failed: Get "http://10.244.1.48:8080/healthz": dial … | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x12 on Pod/recommendations-67c55868cc-2mk82,recommendations-67c55868cc-5f6w2: Readiness probe failed: Get "http://10.244.1.52:8080/hea… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x22 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x11 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-mtscn: Readiness probe failed: Get "http://10.244.1.19:8080/hea… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-5sx5n,pricing-95c99775f-8drxw: Readiness probe failed: Get "http://10.244.1.26:8080/healthz": dial tcp 10.… | O2 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-ckttb: Readiness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:80… | O2 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-5jhhr,edge-6675f7688f-xnt2d: Liveness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1… | O2 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x3 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-mtscn: Liveness probe failed: Get "http://10.244.1.19:8080/healt… | O2 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-13T10:44:49Z — `2026-10-13T10:44:49Z` (O7, prometheus)

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
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O5
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector", "minutes": 30} — test H1 → O6
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O7
  - posteriors: H1=0.38, unexplained=0.62

**Round 2** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.38, unexplained=0.62

**Round 3** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.38, unexplained=0.62

Stop reason: no new evidence for two rounds

</details>