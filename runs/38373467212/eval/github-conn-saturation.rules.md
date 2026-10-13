# RCA: ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service

**Incident:** The checkout service is experiencing a sudden increase in 5xx errors.  
**Namespace:** `shop` · **Investigation:** `20261013-091830-55f1ce` · **Reasoner:** `rules` · 2 rounds, 6 tool calls, 0.5s

## Root cause

ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service

*Hypothesis H1 · component `configmap/checkout-config` · category `configuration`*

**Confidence: MEDIUM** (posterior 0.56). Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.

## Causal chain

1. 'connection' observed: \": dial tcp 10.244.1.20:8080: connect: connection refused", "count": 30, "first (O2)
2. 'pool' observed near checkout-config: odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"}], " (O3)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O2 | kubernetes | weak (+0.5) | `\": dial tcp 10.244.1.20:8080: connect: connection refused", "count": 30, "first_seen": "2026-10-13T09:08:25Z"` | 'connection' observed |
| ✅ O3 | kubernetes | moderate (+0.72) | `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"}], "actor": {"manager": "kub` | 'pool' observed near checkout-config |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T09:04:43.499Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T09:08:22+00:00 | change | rollout/catalog-indexer new-revision | O3 |
| 2026-10-13T09:08:22+00:00 | change | rollout/checkout new-revision | O3 |
| 2026-10-13T09:08:22+00:00 | change | rollout/edge new-revision | O3 |
| 2026-10-13T09:08:22+00:00 | change | rollout/inventory new-revision | O3 |
| 2026-10-13T09:08:22+00:00 | change | rollout/loadgen new-revision | O3 |
| 2026-10-13T09:08:22+00:00 | change | rollout/pricing new-revision | O3 |
| 2026-10-13T09:08:22+00:00 | change | rollout/recommendations new-revision | O3 |
| 2026-10-13T09:08:22+00:00 | change | configmap/edge-waf-rules last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:22+00:00 | change | configmap/feature-flags last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:22+00:00 | change | configmap/kube-root-ca.crt last-write (by kube-controller-manager) | O3 |
| 2026-10-13T09:08:22+00:00 | change | service/catalog-indexer last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:22+00:00 | change | service/checkout last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:22+00:00 | change | service/edge last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:22+00:00 | change | service/inventory last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:22+00:00 | change | service/postgres last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:22+00:00 | change | service/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:22+00:00 | change | service/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:22+00:00 | change | service/telemetry-collector last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-13T09:08:23+00:00 | change | rollout/review-bot new-revision | O3 |
| 2026-10-13T09:08:23+00:00 | change | rollout/telemetry-collector new-revision | O3 |
| 2026-10-13T09:08:25Z | event | event Unhealthy x30 on Pod/checkout-69cf4467b9-2jkkz,checkout-69cf4467b9-h4n6h: Readiness probe failed: Get "http://10.244.1.20:8080/readyz": dial tcp… | O2 |
| 2026-10-13T09:08:26Z | event | event Unhealthy x8 on Pod/edge-5fcdb7c9f5-8bqzf,edge-6675f7688f-l9mbw: Readiness probe failed: Get "http://10.244.1.54:8080/healthz": dial tcp 10.244.… | O2 |
| 2026-10-13T09:08:26Z | event | event Unhealthy x22 on Pod/inventory-5b56655d95-chjbv,inventory-5b56655d95-k2qf4: Readiness probe failed: Get "http://10.244.1.55:8080/healthz": dial … | O2 |
| 2026-10-13T09:08:26Z | event | event Unhealthy x10 on Pod/recommendations-695ff7f988-ctq7f,recommendations-695ff7f988-fhr9m: Readiness probe failed: Get "http://10.244.1.58:8080/hea… | O2 |
| 2026-10-13T09:08:26Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-8b8qg,pricing-95c99775f-wkghm: Readiness probe failed: Get "http://10.244.1.32:8080/healthz": dial tcp 10.… | O2 |
| 2026-10-13T09:08:27Z | event | event Unhealthy x10 on Pod/catalog-indexer-6f6b545fdb-dqrl4,catalog-indexer-6f6b545fdb-n86cb: Readiness probe failed: Get "http://10.244.1.21:8080/hea… | O2 |
| 2026-10-13T09:08:28Z | event | event Unhealthy x2 on Pod/telemetry-collector-865ccb84c6-5xl68: Readiness probe failed: Get "http://10.244.1.37:8080/healthz": dial tcp 10.244.1.37:80… | O2 |
| 2026-10-13T09:08:28Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-l9mbw,edge-6675f7688f-zqq6z: Liveness probe failed: Get "http://10.244.1.27:8080/healthz": dial tcp 10.244.1… | O2 |
| 2026-10-13T09:08:32Z | event | event Unhealthy x3 on Pod/catalog-indexer-6f6b545fdb-dqrl4,catalog-indexer-6f6b545fdb-n86cb: Liveness probe failed: Get "http://10.244.1.21:8080/healt… | O2 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-13T09:13:45Z — `2026-10-13T09:13:45Z` (O6, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.56 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service |

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

**Round 1** — decision: continue; evidence +2 accepted / 0 rejected; new hypotheses ['H1']
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O5
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O6
  - posteriors: H1=0.56, unexplained=0.45

**Round 2** — decision: model judged evidence sufficient; H1 p=0.55 (medium); evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.56, unexplained=0.45

Stop reason: model judged evidence sufficient; H1 p=0.55 (medium)

</details>