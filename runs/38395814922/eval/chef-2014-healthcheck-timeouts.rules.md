# RCA: Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 3, "httpGet": {"path": "/healthz", "port": "http", "scheme": "HTTP"}, "periodSeconds": 10, "successThreshold": 1, "timeoutSeconds": 3}->{"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=1", "port": "http", "scheme": "HTTP"}, "periodSeconds": 5, "successThreshold": 1, "timeoutSeconds": 1}) kills or unreadies healthy pods

**Incident:** Checkout pods keep restarting and the storefront is throwing errors.  
**Namespace:** `shop` · **Investigation:** `20261013-125636-6d25d8` · **Reasoner:** `rules` · 3 rounds, 8 tool calls, 0.5s

## Root cause

Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 3, "httpGet": {"path": "/healthz", "port": "http", "scheme": "HTTP"}, "periodSeconds": 10, "successThreshold": 1, "timeoutSeconds": 3}->{"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=1", "port": "http", "scheme": "HTTP"}, "periodSeconds": 5, "successThreshold": 1, "timeoutSeconds": 1}) kills or unreadies healthy pods

*Hypothesis H1 · component `checkout` · category `probe_misconfiguration`*

**Confidence: INCONCLUSIVE** (posterior 0.30). Inconclusive: no hypothesis is supported well enough to be called the root cause.

## Causal chain

1. 'liveness probe failed' observed near checkout: heckout-7d6bdccdc8-wd72m"], "message": "Liveness probe failed: Get \"http://10.2 (O4)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O4 | kubernetes | moderate (+1.2) | `heckout-7d6bdccdc8-wd72m"], "message": "Liveness probe failed: Get \"http://10.244.1.82:8080/healthz?deep=1\":…` | 'liveness probe failed' observed near checkout |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T12:17:30.161Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T12:21:15Z | event | event Unhealthy x87 on Pod/checkout-69cf4467b9-j69d5,checkout-69cf4467b9-k5j84: Readiness probe failed: Get "http://10.244.1.22:8080/readyz": dial tcp… | O4 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x18 on Pod/edge-6675f7688f-cvj8l,edge-6675f7688f-xz97h: Readiness probe failed: Get "http://10.244.1.23:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x52 on Pod/inventory-5fd7bfd5d5-4vmdt,inventory-5fd7bfd5d5-7qlt7: Readiness probe failed: Get "http://10.244.1.73:8080/healthz": dial … | O4 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x20 on Pod/recommendations-58866dbd86-8wlzh,recommendations-58866dbd86-9gsgr: Readiness probe failed: Get "http://10.244.1.54:8080/hea… | O4 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x19 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-rpmzl: Readiness probe failed: Get "http://10.244.1.18:8080/hea… | O4 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x4 on Pod/pricing-95c99775f-8v97j,pricing-95c99775f-fkzqq: Readiness probe failed: Get "http://10.244.1.29:8080/healthz": dial tcp 10.… | O4 |
| 2026-10-13T12:21:17Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-vwkb8: Readiness probe failed: Get "http://10.244.1.37:8080/healthz": dial tcp 10.244.1.37:80… | O4 |
| 2026-10-13T12:21:18Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-cvj8l,edge-6675f7688f-xz97h: Liveness probe failed: Get "http://10.244.1.23:8080/healthz": dial tcp 10.244.1… | O4 |
| 2026-10-13T12:21:23Z | event | event Unhealthy x5 on Pod/catalog-indexer-6f6b545fdb-fcs76,catalog-indexer-6f6b545fdb-rpmzl: Liveness probe failed: Get "http://10.244.1.18:8080/healt… | O4 |
| 2026-10-13T12:21:23Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-j69d5,checkout-69cf4467b9-k5j84: Liveness probe failed: Get "http://10.244.1.22:8080/healthz": dial tcp … | O4 |
| 2026-10-13T12:21:28Z | event | event FailedGetResourceMetric x2 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O4 |
| 2026-10-13T12:21:28Z | event | event FailedComputeMetricsReplicas x2 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T12:21:30Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O4 |
| 2026-10-13T12:21:43Z | event | event FailedGetResourceMetric x4 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods might… | O4 |
| 2026-10-13T12:21:43Z | event | event FailedComputeMetricsReplicas x4 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T12:26:23Z | event | event FailedKillPod x1 on Pod/checkout-69cf4467b9-k5j84: error killing pod: [failed to "KillContainer" for "checkout" with KillContainerError: "rpc… | O4 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x2 on Pod/checkout-8457f655f7-jwzw6,checkout-8457f655f7-nmx9x: Failed to create pod sandbox: rpc error: code = Unavailabl… | O4 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x1 on Pod/edge-959ccbf85-khbs6: Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from ser… | O4 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x2 on Pod/inventory-668745bb49-psdmx,inventory-668745bb49-s52z8: Failed to create pod sandbox: rpc error: code = Unavaila… | O4 |
| 2026-10-13T12:26:23Z | event | event FailedKillPod x1 on Pod/inventory-6ffc77fd45-5cmsp: error killing pod: [failed to "KillContainer" for "inventory" with KillContainerError: "rp… | O4 |
| 2026-10-13T12:26:23Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc … | O4 |
| 2026-10-13T12:26:23Z | event | event FailedCreatePodSandBox x1 on Pod/recommendations-58866dbd86-9gsgr: Failed to create pod sandbox: rpc error: code = Unavailable desc = error read… | O4 |
| 2026-10-13T12:26:30Z | event | event Unhealthy x1 on Pod/edge-6675f7688f-cvj8l: Readiness probe failed: Get "http://10.244.1.23:8080/healthz": context deadline exceeded (… | O4 |
| 2026-10-13T12:29:51+00:00 | change | service/telemetry-collector-v2 created (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:29:51Z | change | service/telemetry-collector deleted | O2 |
| 2026-10-13T12:42:34Z | change | service/telemetry-collector-v2 deleted | O2 |
| 2026-10-13T12:42:35+00:00 | change | service/telemetry-collector created (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:42:36+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-roll… | O2 |
| 2026-10-13T12:42:36+00:00 | change | deployment/edge modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O2 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-13T12:46:06Z — `2026-10-13T12:46:06Z` (O7, prometheus)
- checkout error_ratio_5xx increase at 2026-10-13T12:42:51Z — `2026-10-13T12:42:51Z` (O8, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.30 | cause | probe_misconfiguration | active | +1/−0 | kubernetes | Probe change on checkout (containers[checkout].livenessProbe {"failureThreshold": 3, "httpGet": {"path": "/healthz", "po… |
| H3 | 0.30 | cause | dependency | active | +1/−0 | kubernetes | Service checkout has no healthy backends |
| H2 | 0.15 | cause | dependency | active | +1/−0 | kubernetes | Service telemetry-collector-v2 was deleted () so callers cannot reach it |

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (weak, O4/kubernetes): `\": dial tcp 10.244.1.82:8080: connect: connection refused", "count": 11, "first_seen": "2026-10-13T…` — 'connection refused' observed
- H3 supports (moderate, O4/kubernetes): `\": dial tcp 10.244.1.82:8080: connect: connection refused", "count": 11, "first_seen": "2026-10-13T…` — 'connection refused' observed near checkout

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

**Round 1** — decision: continue; evidence +3 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O5
  - `workload_metrics` {"namespace": "shop", "workload": "telemetry-collector-v2", "minutes": 30} — test H2 → O6
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O7
  - `workload_metrics` {"namespace": "shop", "workload": "checkout", "minutes": 30} — test H1 → O8
  - posteriors: H1=0.30, H2=0.15, H3=0.30, unexplained=0.25

**Round 2** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.30, H2=0.15, H3=0.30, unexplained=0.25

**Round 3** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.30, H2=0.15, H3=0.30, unexplained=0.25

Stop reason: no new evidence for two rounds

</details>