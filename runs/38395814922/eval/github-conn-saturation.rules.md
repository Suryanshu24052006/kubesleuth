# RCA: ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service

**Incident:** The checkout service is experiencing a sudden increase in 5xx errors.  
**Namespace:** `shop` · **Investigation:** `20261013-131617-a327d7` · **Reasoner:** `rules` · 3 rounds, 7 tool calls, 0.8s

## Root cause

ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service

*Hypothesis H1 · component `configmap/checkout-config` · category `configuration`*

**Confidence: LOW** (posterior 0.41). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. 'pool' observed near checkout-config: odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30", "in (O2)
2. 'connection' observed: \": dial tcp 10.244.1.91:8080: connect: connection refused", "count": 112, "firs (O4)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O2 | kubernetes | moderate (+1.2) | `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30", "in_effect": true}], "actor` | 'pool' observed near checkout-config |
| ✅ O4 | kubernetes | weak (+0.3) | `\": dial tcp 10.244.1.91:8080: connect: connection refused", "count": 112, "first_seen": "2026-10-13T12:21:15Z` | 'connection' observed |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T12:17:30.161Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T12:21:15Z | event | event Unhealthy x112 on Pod/checkout-55f8c5b4bc-6ssw7,checkout-55f8c5b4bc-bqhj9: Readiness probe failed: Get "http://10.244.1.91:8080/readyz": dial tc… | O4 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x53 on Pod/edge-6675f7688f-cvj8l,edge-6675f7688f-xz97h: Readiness probe failed: Get "http://10.244.1.23:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x65 on Pod/inventory-5577665986-4q7mj,inventory-5577665986-9g7mx: Readiness probe failed: Get "http://10.244.1.106:8080/healthz": dial… | O4 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x28 on Pod/recommendations-54c5f6ddff-7fvrl,recommendations-54c5f6ddff-8nwmm: Readiness probe failed: Get "http://10.244.1.100:8080/he… | O4 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x19 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-rpmzl: Readiness probe failed: Get "http://10.244.1.18:8080/hea… | O4 |
| 2026-10-13T12:21:23Z | event | event Unhealthy x5 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-rpmzl: Liveness probe failed: Get "http://10.244.1.18:8080/healt… | O4 |
| 2026-10-13T12:21:28Z | event | event FailedGetResourceMetric x7 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O4 |
| 2026-10-13T12:21:28Z | event | event FailedComputeMetricsReplicas x7 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T12:21:43Z | event | event FailedGetResourceMetric x10 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods migh… | O4 |
| 2026-10-13T12:21:43Z | event | event FailedComputeMetricsReplicas x10 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resour… | O4 |
| 2026-10-13T12:26:30Z | event | event Unhealthy x34 on Pod/edge-6675f7688f-cvj8l,edge-66978949cf-2m5mj: Readiness probe failed: Get "http://10.244.1.23:8080/healthz": context deadlin… | O4 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x9 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (… | O4 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x5 on Pod/inventory-6dcd8d4f55-vb8z7: Liveness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (C… | O4 |
| 2026-10-13T12:47:02Z | event | event Unhealthy x1 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": read tcp 10.244.1.1:52866->… | O4 |
| 2026-10-13T12:50:07Z | event | event Unhealthy x1 on Pod/checkout-6cc8cb7b8c-9kcll: Readiness probe failed: Get "http://10.244.1.60:8080/readyz": context deadline exceeded (C… | O4 |
| 2026-10-13T12:54:38Z | event | event Unhealthy x3 on Pod/checkout-7d6bdccdc8-7qz6f,checkout-7d6bdccdc8-r6c2x: Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": co… | O4 |
| 2026-10-13T12:54:42Z | event | event Unhealthy x11 on Pod/checkout-7d6bdccdc8-7qz6f,checkout-7d6bdccdc8-r6c2x: Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": d… | O4 |
| 2026-10-13T12:55:16Z | event | event BackOff x17 on Pod/checkout-7d6bdccdc8-wd72m: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-wd72m_shop(41dd06… | O4 |
| 2026-10-13T12:55:16Z | event | event BackOff x3 on Pod/checkout-7d6bdccdc8-7qz6f: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-7qz6f_shop(0d8ee6… | O4 |
| 2026-10-13T12:55:17Z | event | event BackOff x18 on Pod/checkout-7d6bdccdc8-r6c2x: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-r6c2x_shop(94ba00… | O4 |
| 2026-10-13T12:56:03Z | onset | edge dependency_failures_rps on 2/3 series increase: 0.0 → 2.0 | O5 |
| 2026-10-13T12:59:28+00:00 | change | deployment/checkout modified: containers[checkout].livenessProbe {"failureThreshold": 1, "httpG… → {"failureThreshold": 3, "httpG… (by kubectl-client-… | O2 |
| 2026-10-13T12:59:29+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-roll… | O2 |
| 2026-10-13T12:59:29+00:00 | change | deployment/edge modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O2 |
| 2026-10-13T12:59:29+00:00 | change | deployment/recommendations modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubec… | O2 |
| 2026-10-13T12:59:29+00:00 | change | deployment/inventory modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rol… | O2 |
| 2026-10-13T12:59:29+00:00 | change | deployment/edge modified: spec.replicas 2 → 3 (by kubectl-rollout) | O2 |
| 2026-10-13T12:59:29+00:00 | change | rollout/checkout new-revision: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… | O2 |
| 2026-10-13T12:59:29+00:00 | change | rollout/edge new-revision: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… | O2 |

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.41 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service |
| H2 | 0.20 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap edge-waf-rules change (data.rules.json {"rules": [ {"id": "sqli-union-select", "pattern": "(?i)union\\s+select… |
| H3 | 0.15 | cause | probe_misconfiguration | active | +1/−0 | kubernetes | Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=… |

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (weak, O2/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30", "in_effect": true}], "a…` — 'pool' observed
- H2 supports (weak, O4/kubernetes): `\": dial tcp 10.244.1.91:8080: connect: connection refused", "count": 112, "first_seen": "2026-10-13…` — 'connection' observed
- H3 supports (weak, O4/kubernetes): `, "edge-66978949cf-m4mtr"], "message": "Liveness probe failed: Get \"http://10.244.1.97:8080/healthz…` — 'liveness probe failed' observed

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
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O2
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: continue; evidence +5 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O5
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O6
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H3 → O7
  - posteriors: H1=0.41, H2=0.20, H3=0.15, unexplained=0.24

**Round 2** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.41, H2=0.20, H3=0.15, unexplained=0.24

**Round 3** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.41, H2=0.20, H3=0.15, unexplained=0.24

Stop reason: no new evidence for two rounds

</details>