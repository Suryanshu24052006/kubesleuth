# RCA: ConfigMap edge-waf-rules change (data.rules.json {"rules": [
  {"id": "sqli-union-select", "pattern": "(?i)union\\s+select", "action": "block"},
  {"id": "path-traversal", "pattern": "\\.\\./\\.\\./", "action": "block"}
]}
->{"rules": [
  {"id": "sqli-union-select", "pattern": "(?i)union\\s+select", "action": "block"},
  {"id": "path-traversal", "pattern": "\\.\\./\\.\\./", "action": "block"},
  {"id": "xss-inline-js-2019-07", "pattern": "(?:(?:\\\"|'|\\]|\\}|\\\\|\\d|(?:nan|infinity|true|false|null|undefined|symbol|math)|\\`|\\-|\\+)+[)]*;?((?:\\s|-|~|!|{}|\\|\\||\\+)*.*(?:.*=.*)))", "action": "log"}
]}) broke a dependent service

**Incident:** The edge service latency and error rate spiked; customers report timeouts.  
**Namespace:** `shop` · **Investigation:** `20261013-130447-d9ee44` · **Reasoner:** `rules` · 3 rounds, 7 tool calls, 1.0s

## Root cause

ConfigMap edge-waf-rules change (data.rules.json {"rules": [
  {"id": "sqli-union-select", "pattern": "(?i)union\\s+select", "action": "block"},
  {"id": "path-traversal", "pattern": "\\.\\./\\.\\./", "action": "block"}
]}
->{"rules": [
  {"id": "sqli-union-select", "pattern": "(?i)union\\s+select", "action": "block"},
  {"id": "path-traversal", "pattern": "\\.\\./\\.\\./", "action": "block"},
  {"id": "xss-inline-js-2019-07", "pattern": "(?:(?:\\\"|'|\\]|\\}|\\\\|\\d|(?:nan|infinity|true|false|null|undefined|symbol|math)|\\`|\\-|\\+)+[)]*;?((?:\\s|-|~|!|{}|\\|\\||\\+)*.*(?:.*=.*)))", "action": "log"}
]}) broke a dependent service

*Hypothesis H1 · component `configmap/edge-waf-rules` · category `configuration`*

**Confidence: INCONCLUSIVE** (posterior 0.27). Inconclusive: no hypothesis is supported well enough to be called the root cause.

## Causal chain

1. 'connection' observed: \": dial tcp 10.244.1.23:8080: connect: connection refused", "count": 32, "first (O2)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O2 | kubernetes | weak (+0.5) | `\": dial tcp 10.244.1.23:8080: connect: connection refused", "count": 32, "first_seen": "2026-10-13T12:21:16Z"` | 'connection' observed |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T12:17:30.161Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T12:21:15Z | event | event Unhealthy x104 on Pod/checkout-55f8c5b4bc-6ssw7,checkout-55f8c5b4bc-bqhj9: Readiness probe failed: Get "http://10.244.1.91:8080/readyz": dial tc… | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x32 on Pod/edge-6675f7688f-cvj8l,edge-6675f7688f-xz97h: Readiness probe failed: Get "http://10.244.1.23:8080/healthz": dial tcp 10.244… | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x58 on Pod/inventory-5fd7bfd5d5-4vmdt,inventory-5fd7bfd5d5-7qlt7: Readiness probe failed: Get "http://10.244.1.73:8080/healthz": dial … | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x24 on Pod/recommendations-58866dbd86-8wlzh,recommendations-58866dbd86-9gsgr: Readiness probe failed: Get "http://10.244.1.54:8080/hea… | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x19 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-rpmzl: Readiness probe failed: Get "http://10.244.1.18:8080/hea… | O2 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x4 on Pod/pricing-95c99775f-8v97j,pricing-95c99775f-fkzqq: Readiness probe failed: Get "http://10.244.1.29:8080/healthz": dial tcp 10.… | O2 |
| 2026-10-13T12:21:17Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-vwkb8: Readiness probe failed: Get "http://10.244.1.37:8080/healthz": dial tcp 10.244.1.37:80… | O2 |
| 2026-10-13T12:21:18Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-cvj8l,edge-6675f7688f-xz97h: Liveness probe failed: Get "http://10.244.1.23:8080/healthz": dial tcp 10.244.1… | O2 |
| 2026-10-13T12:21:23Z | event | event Unhealthy x5 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-rpmzl: Liveness probe failed: Get "http://10.244.1.18:8080/healt… | O2 |
| 2026-10-13T12:21:23Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-j69d5,checkout-69cf4467b9-k5j84: Liveness probe failed: Get "http://10.244.1.22:8080/healthz": dial tcp … | O2 |
| 2026-10-13T12:21:28Z | event | event FailedGetResourceMetric x2 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O2 |
| 2026-10-13T12:21:28Z | event | event FailedComputeMetricsReplicas x2 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O2 |
| 2026-10-13T12:21:30Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O2 |
| 2026-10-13T12:21:43Z | event | event FailedGetResourceMetric x8 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods might… | O2 |
| 2026-10-13T12:21:43Z | event | event FailedComputeMetricsReplicas x8 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O2 |
| 2026-10-13T12:26:23Z | event | event FailedKillPod x1 on Pod/checkout-69cf4467b9-k5j84: error killing pod: [failed to "KillContainer" for "checkout" with KillContainerError: "rpc… | O2 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x2 on Pod/checkout-8457f655f7-jwzw6,checkout-8457f655f7-nmx9x: Failed to create pod sandbox: rpc error: code = Unavailabl… | O2 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x1 on Pod/edge-959ccbf85-khbs6: Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from ser… | O2 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x2 on Pod/inventory-668745bb49-psdmx,inventory-668745bb49-s52z8: Failed to create pod sandbox: rpc error: code = Unavaila… | O2 |
| 2026-10-13T12:26:23Z | event | event FailedKillPod x1 on Pod/inventory-6ffc77fd45-5cmsp: error killing pod: [failed to "KillContainer" for "inventory" with KillContainerError: "rp… | O2 |
| 2026-10-13T12:26:23Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc … | O2 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x1 on Pod/recommendations-58866dbd86-9gsgr: Failed to create pod sandbox: rpc error: code = Unavailable desc = error read… | O2 |
| 2026-10-13T12:26:30Z | event | event Unhealthy x24 on Pod/edge-6675f7688f-cvj8l,edge-66978949cf-2m5mj: Readiness probe failed: Get "http://10.244.1.23:8080/healthz": context deadlin… | O2 |
| 2026-10-13T12:42:36+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-roll… | O4 |
| 2026-10-13T12:42:36+00:00 | change | deployment/edge modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O4 |
| 2026-10-13T12:42:48Z | onset | checkout error_ratio_5xx increase: 0.0 → 0.002235 | O7 |
| 2026-10-13T12:42:48Z | onset | checkout dependency_failures_rps on 2/3 series increase: 0.0 → 0.036072 | O7 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x9 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (… | O2 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x5 on Pod/inventory-6dcd8d4f55-vb8z7: Liveness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (C… | O2 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-13T12:46:03Z — `2026-10-13T12:46:03Z` (O6, prometheus)
- checkout error_ratio_5xx increase at 2026-10-13T12:42:48Z — `2026-10-13T12:42:48Z` (O7, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.27 | cause | configuration | active | +1/−0 | kubernetes | ConfigMap edge-waf-rules change (data.rules.json {"rules": [ {"id": "sqli-union-select", "pattern": "(?i)union\\s+select… |
| H2 | 0.27 | cause | probe_misconfiguration | active | +1/−0 | kubernetes | Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=… |

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (weak, O2/kubernetes): `, "edge-66978949cf-m4mtr"], "message": "Liveness probe failed: Get \"http://10.244.1.97:8080/healthz…` — 'liveness probe failed' observed

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

**Round 1** — decision: continue; evidence +2 accepted / 0 rejected; new hypotheses ['H1', 'H2']
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O5
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O6
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H2 → O7
  - posteriors: H1=0.27, H2=0.27, unexplained=0.45

**Round 2** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.27, H2=0.27, unexplained=0.45

**Round 3** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.27, H2=0.27, unexplained=0.45

Stop reason: no new evidence for two rounds

</details>