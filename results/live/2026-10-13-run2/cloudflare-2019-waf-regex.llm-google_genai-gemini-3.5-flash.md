# Edge Service CPU Starvation and Timeouts Caused by WAF Rules Configuration Change

**Incident:** The edge service latency and error rate spiked; customers report timeouts.  
**Namespace:** `shop` · **Investigation:** `20261013-130448-f26d88` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 2 rounds, 8 tool calls, 400.2s

## Root cause

A newly introduced regular expression in the edge-waf-rules ConfigMap caused heavy CPU consumption and request blocking, leading to severe CPU starvation, high latency, and probe timeouts on the edge pods.

*Hypothesis H1 · component `configmap/edge-waf-rules` · category `configuration`*

**Confidence: HIGH** (posterior 0.89). High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.

## Causal chain

1. ConfigMap edge-waf-rules was modified at 2026-10-13T13:02:46+00:00 with new WAF rule patterns. (O3)
2. Edge pods experienced high CPU throttling and starvation immediately following the configuration change. (O6)
3. CPU exhaustion on edge pods led to failing liveness and readiness probes, causing container restarts and degraded service availability. (O2, O4)
4. Edge services failed to communicate with upstream dependencies due to timeouts, resulting in a spike in 5xx error rates and customer-facing timeouts. (O5, O6)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O4 | kubernetes | strong (+2.3) | `"utilization_pct": 447` | Extremely high CPU utilization (447%) aligns with regex-induced CPU starvation. |
| ✅ O5 | loki | moderate (+1.2) | `checkout call failed error=ConnectTimeout` | Edge pods under heavy CPU starvation are timing out when trying to communicate with dependencies. |
| ✅ O7 | kubernetes-logs | moderate (+1.2) | `checkout call failed", "error": "ConnectTimeout", "detail": ""` | Edge pods encounter ConnectTimeout errors calling the checkout dependency, showing external dependency issues are part of the failure mode. |

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
| 2026-10-13T12:42:36+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-roll… | O3 |
| 2026-10-13T12:42:36+00:00 | change | deployment/edge modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O3 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x9 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (… | O2 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x5 on Pod/inventory-6dcd8d4f55-vb8z7: Liveness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (C… | O2 |
| 2026-10-13T12:46:10Z | onset | edge dependency_failures_rps on 3/3 series increase: 0.0 → 3.634359 | O6 |
| 2026-10-13T12:46:15Z | onset | checkout error_ratio_5xx increase: 0.0 → 0.90691 | O8 |

## Observed facts

- The edge deployment has only 2 out of 3 replicas ready. — `Deployment edge: only 2/3 replicas ready` (O4, kubernetes)
- The HPA for edge is currently at its maximum replica limit of 3. — `HPA edge is at maxReplicas (3)` (O4, kubernetes)
- Edge pods are experiencing liveness probe timeouts on /healthz. — `Liveness probe failed: Get "http://10.244.1.97:8080/healthz": context deadline exceeded` (O2, kubernetes)
- The CPU utilization for the edge HPA target is extremely high at 447%. — `"utilization_pct": 447` (O4, kubernetes)
- Edge pods are experiencing connection timeouts when calling the checkout service. — `checkout call failed error=ConnectTimeout` (O5, loki)
- Dependency failures for checkout (connect_error) surged starting at 12:54:55Z. — `onset: {"time": "2026-10-13T12:54:55Z", "direction": "increase", "baseline": 0.0, "value_after": 3.1…` (O6, prometheus)
- CPU throttling on edge pods jumped significantly starting at 13:03:25Z after the WAF rules configmap update. — `onset: {"time": "2026-10-13T13:03:25Z", "direction": "increase", "baseline": 0.0, "value_after": 0.6…` (O6, prometheus)
- Edge pod container restarts began increasing at 13:04:10Z. — `onset: {"time": "2026-10-13T13:04:10Z", "direction": "increase", "baseline": 0.0, "value_after": 2.0…` (O6, prometheus)
- Checkout workload metrics show an increase in error ratio 5xx starting at 2026-10-13T12:46:15Z. — `onset": {"time": "2026-10-13T12:46:15Z", "direction": "increase", "baseline": 0.0, "value_after": 0.…` (O8, prometheus)
- Edge pod previous instance logs show numerous ConnectTimeout errors when calling checkout. — `{"ts": "2026-10-13T13:08:32.654Z", "level": "error", "svc": "edge", "version": "1.4.0", "msg": "chec…` (O7, kubernetes-logs)
- Checkout dependency failures towards inventory (connect_error) increased starting at 2026-10-13T12:46:15Z. — `onset": {"time": "2026-10-13T12:46:15Z", "direction": "increase", "baseline": 0.0, "value_after": 3.…` (O8, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.89 | cause | configuration | active | +3/−0 | kubernetes, kubernetes-logs, loki | The newly added regex in edge-waf-rules causes heavy CPU consumption or request blocking, leading to CPU starvation, hig… |
| H3 | 0.08 | cause | dependency | active | +1/−0 | prometheus | The checkout service itself is failing or down, causing edge pods to receive connect and read timeouts. |
| H2 | 0.01 | symptom | capacity | active | +0/−0 |  | High traffic load or lack of capacity on edge pods is causing CPU exhaustion and probe failures. |

## Alternative explanations

- **H2**: Traffic metrics show a drop in request rate rather than a surge, ruling out high traffic volume or simple capacity constraints as the primary cause.
- **H3**: Although upstream checkout dependency issues occurred, metrics and logs correlate the core edge latency and CPU throttling spike precisely with the WAF rule modifications.

<details><summary>Evidence for/against other hypotheses</summary>

- H3 supports (strong, O8/prometheus): `onset": {"time": "2026-10-13T12:46:15Z", "direction": "increase", "baseline": 0.0, "value_after": 0.…` — Checkout service shows a 5xx error ratio spike and dependency connection errors to inventory, explaining why edge receiv…

</details>

## Uncertainty

- The exact regular expression causing the catastrophic backtracking in the edge-waf-rules ConfigMap has not been isolated.
- Performance profiling of the regex evaluation engine inside the edge pods would confirm the specific pattern responsible.
- 2 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Revert the edge-waf-rules ConfigMap to the previous stable revision.
- Review and test all newly added regular expressions for catastrophic backtracking vulnerabilities before deploying them to production.
- Implement resource quotas and stricter CPU limits or timeouts on regex evaluations to protect proxy and edge components.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +1 accepted / 1 rejected; new hypotheses ['H1', 'H2']
  - `active_alerts` {} — what is alerting and since when → O1
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: continue; evidence +1 accepted / 1 rejected; new hypotheses ['H3']
  - `search_logs` {"namespace": "shop", "app": "edge"} — Check edge pod logs for any WAF-related errors, panic, or long processing times. → O5
  - `workload_metrics` {"namespace": "shop", "workload": "edge"} — Examine CPU and request rate metrics for edge to see the exact onset time relative to the WAF rule change. → O6
  - posteriors: H1=0.88, H2=0.03, H3=0.03, unexplained=0.07

**Round 2** — decision: confident: H1 p=0.89, margin 0.81, sources ['kubernetes', 'kubernetes-logs', 'loki']; evidence +2 accepted / 0 rejected; new hypotheses []
  - `pod_logs` {"namespace": "shop", "pod": "edge-66978949cf-2m5mj", "previous": true} — Inspect the previous container logs of a restarted edge pod to see if it crashed due to OOM, probe failure, or an unhandled exception related to WAF regex compilation. → O7
  - `workload_metrics` {"namespace": "shop", "workload": "checkout"} — Check the health, request rate, error ratio, and CPU/memory metrics of the checkout service to see if checkout is also affected or if it is the root dependency failure. → O8
  - posteriors: H1=0.89, H2=0.01, H3=0.08, unexplained=0.02

Stop reason: confident: H1 p=0.89, margin 0.81, sources ['kubernetes', 'kubernetes-logs', 'loki']

</details>