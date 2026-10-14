# RCA: ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service

**Incident:** The checkout service is experiencing a sudden increase in 5xx errors.  
**Namespace:** `shop` · **Investigation:** `20261014-084102-ddcf98` · **Reasoner:** `rules` · 3 rounds, 8 tool calls, 0.3s

## Root cause

ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service

*Hypothesis H1 · component `configmap/checkout-config` · category `configuration`*

**Confidence: INCONCLUSIVE** (posterior 0.29). Inconclusive: no hypothesis is supported well enough to be called the root cause.

## Causal chain

1. 'connection' observed: \": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 71, "first (O2)
2. 'pool' observed near checkout-config: odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30", "in (O3)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O2 | kubernetes | weak (+0.5) | `\": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 71, "first_seen": "2026-10-14T07:53:33Z"` | 'connection' observed |
| ✅ O3 | kubernetes | moderate (+0.72) | `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30", "in_effect": true}], "actor` | 'pool' observed near checkout-config |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-14T07:49:52.298Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-14T07:53:30+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (since reverted) (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/inventory modified: spec.replicas 4 → 1 (since reverted) (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/edge modified: spec.replicas 2 → 3 (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/catalog-indexer new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/checkout new-revision: containers[checkout].livenessProbe {"failureThreshold": 1, "httpG… → {"failureThreshold": 3, "httpG… | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/edge new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/inventory new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/loadgen new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/pricing new-revision | O3 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x71 on Pod/checkout-68fb58bcfd-92lpn,checkout-68fb58bcfd-jlw7x: Readiness probe failed: Get "http://10.244.1.50:8080/readyz": dial tcp… | O2 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x10 on Pod/edge-6675f7688f-btmm6,edge-6675f7688f-dtglc: Readiness probe failed: Get "http://10.244.1.56:8080/healthz": dial tcp 10.244… | O2 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x16 on Pod/catalog-indexer-6f6b545fdb-27c8g,catalog-indexer-6f6b545fdb-7gbtg: Readiness probe failed: Get "http://10.244.1.44:8080/hea… | O2 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x23 on Pod/inventory-6ffc77fd45-28b67,inventory-6ffc77fd45-5hvm2: Readiness probe failed: Get "http://10.244.1.27:8080/healthz": dial … | O2 |
| 2026-10-14T07:53:34Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-rtmsj,pricing-95c99775f-z5psf: Readiness probe failed: Get "http://10.244.1.32:8080/healthz": dial tcp 10.… | O2 |
| 2026-10-14T07:53:34Z | event | event Unhealthy x6 on Pod/recommendations-7bd4dd95d6-gfbqx,recommendations-7bd4dd95d6-pxghg: Readiness probe failed: Get "http://10.244.1.34:8080/heal… | O2 |
| 2026-10-14T07:53:34Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-htm9x: Readiness probe failed: Get "http://10.244.1.37:8080/healthz": dial tcp 10.244.1.37:80… | O2 |
| 2026-10-14T07:53:35Z | event | event Unhealthy x1 on Pod/edge-6675f7688f-dtglc: Liveness probe failed: Get "http://10.244.1.22:8080/healthz": dial tcp 10.244.1.22:8080: c… | O2 |
| 2026-10-14T07:53:40Z | event | event Unhealthy x3 on Pod/catalog-indexer-6f6b545fdb-7gbtg,catalog-indexer-6f6b545fdb-pmnvz: Liveness probe failed: Get "http://10.244.1.20:8080/healt… | O2 |
| 2026-10-14T07:53:40Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-2cjfb,checkout-69cf4467b9-mtmgb: Liveness probe failed: Get "http://10.244.1.25:8080/healthz": dial tcp … | O2 |
| 2026-10-14T07:53:43Z | event | event FailedCreatePodSandBox x1 on Pod/postgres-0: Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from serv… | O2 |
| 2026-10-14T07:53:45Z | event | event FailedGetResourceMetric x2 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O2 |
| 2026-10-14T07:53:45Z | event | event FailedComputeMetricsReplicas x2 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O2 |
| 2026-10-14T07:53:45Z | event | event InspectFailed x1 on Pod/postgres-0: Failed to inspect image "": rpc error: code = Unavailable desc = connection error: desc = … | O2 |
| 2026-10-14T07:53:45Z | event | event Failed x1 on Pod/postgres-0: Error: ImageInspectError | O2 |
| 2026-10-14T07:53:50Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O2 |
| 2026-10-14T08:01:26+00:00 | change | service/telemetry-collector-v2 created (by kubectl-client-side-apply) | O3 |
| 2026-10-14T08:01:26Z | change | service/telemetry-collector deleted | O3 |
| 2026-10-14T08:12:26Z | change | service/telemetry-collector-v2 deleted | O3 |
| 2026-10-14T08:12:27+00:00 | change | service/telemetry-collector created (by kubectl-client-side-apply) | O3 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-14T08:23:33Z — `2026-10-14T08:23:33Z` (O7, prometheus)
- checkout error_ratio_5xx increase at 2026-10-14T08:18:03Z — `2026-10-14T08:18:03Z` (O8, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.29 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service |
| H2 | 0.19 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap edge-waf-rules change (data.rules.json {"rules": [ {"id": "sqli-union-select", "pattern": "(?i)union\\s+select… |
| H3 | 0.14 | cause | probe_misconfiguration | active | +1/−0 | kubernetes | Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=… |
| H4 | 0.14 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector-v2 was deleted () so callers cannot reach it |

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (weak, O2/kubernetes): `\": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 71, "first_seen": "2026-10-14T…` — 'connection' observed
- H3 supports (weak, O2/kubernetes): `, "edge-6675f7688f-rvxfg"], "message": "Liveness probe failed: Get \"http://10.244.1.22:8080/healthz…` — 'liveness probe failed' observed
- H4 supports (weak, O2/kubernetes): `\": dial tcp 10.244.1.50:8080: connect: connection refused", "count": 71, "first_seen": "2026-10-14T…` — 'connection refused' observed
- H2 supports (weak, O3/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30", "in_effect": true}], "a…` — 'pool' observed

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

**Round 1** — decision: continue; evidence +6 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3', 'H4']
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector-v2", "minutes": 30} — test H4 → O5
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O6
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O7
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H3 → O8
  - posteriors: H1=0.29, H2=0.19, H3=0.14, H4=0.14, unexplained=0.23

**Round 2** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.29, H2=0.19, H3=0.14, H4=0.14, unexplained=0.23

**Round 3** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.29, H2=0.19, H3=0.14, H4=0.14, unexplained=0.23

Stop reason: no new evidence for two rounds

</details>