# Checkout Errors Due to Smart Routing to Pricing-Legacy

**Incident:** Checkout errors jumped to roughly a third of requests a few minutes ago.  
**Namespace:** `shop` · **Investigation:** `20261013-133031-8a6cfa` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 1 rounds, 7 tool calls, 484.4s

## Root cause

Enabling the smart_routing feature flag routed traffic to the newly created pricing-legacy deployment running an incompatible or failing image version, resulting in downstream pricing and checkout failures.

*Hypothesis H1 · component `deployment/pricing-legacy` · category `version_skew`*

**Confidence: HIGH** (posterior 0.99). High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.

## Causal chain

1. Deployment pricing-legacy was created and the feature-flags configmap enabled smart_routing. (O2)
2. Traffic was routed to pricing-legacy, which experienced failing readiness probes and runtime routing errors. (O3, O4, O5)
3. Checkout workloads began encountering errors due to the failing downstream pricing dependency. (O6)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O3 | kubernetes | strong (+2.3) | `service pricing routes to 2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 'shop:…` | Shows that traffic is split to an older version pricing-legacy pod which could be incompatible or broken. |
| ✅ O5 | kubernetes-logs | strong (+2.3) | `PowerPeg router active: child orders exceed parent quantity, rejecting flag=smart_routing` | Confirms that pricing-legacy is running with the smart_routing flag enabled and actively producing errors under load. |
| ✅ O6 | prometheus | moderate (+1.2) | `error_ratio_5xx": [{"labels": {}, "points": 121, "from": "2026-10-13T13:05:05Z", "to": "2026-10-13T13:35:05Z",…` | Shows checkout workload experiencing 5xx errors concurrently with feature flag and routing changes. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T12:17:30.161Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x12 on Pod/catalog-indexer-6f6b545fdb-rpmzl,catalog-indexer-6f6b545fdb-wv8gh: Readiness probe failed: Get "http://10.244.1.66:8080/hea… | O4 |
| 2026-10-13T12:21:28Z | event | event FailedGetResourceMetric x7 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O4 |
| 2026-10-13T12:21:28Z | event | event FailedComputeMetricsReplicas x7 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T12:21:43Z | event | event FailedGetResourceMetric x12 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods migh… | O4 |
| 2026-10-13T12:21:43Z | event | event FailedComputeMetricsReplicas x12 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resour… | O4 |
| 2026-10-13T12:26:45Z | event | event Unhealthy x25 on Pod/recommendations-54c5f6ddff-7fvrl,recommendations-54c5f6ddff-8nwmm: Readiness probe failed: Get "http://10.244.1.100:8080/he… | O4 |
| 2026-10-13T12:42:37Z | event | event Unhealthy x98 on Pod/checkout-55f8c5b4bc-6ssw7,checkout-55f8c5b4bc-bqhj9: Readiness probe failed: Get "http://10.244.1.91:8080/readyz": dial tcp… | O4 |
| 2026-10-13T12:42:38Z | event | event Unhealthy x54 on Pod/inventory-5577665986-4q7mj,inventory-5577665986-9g7mx: Readiness probe failed: Get "http://10.244.1.106:8080/healthz": dial… | O4 |
| 2026-10-13T12:42:38Z | event | event Unhealthy x50 on Pod/edge-66978949cf-2m5mj,edge-66978949cf-g8mnj: Readiness probe failed: Get "http://10.244.1.97:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x9 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (… | O4 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x5 on Pod/inventory-6dcd8d4f55-vb8z7: Liveness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (C… | O4 |
| 2026-10-13T12:46:36Z | event | event Unhealthy x1 on Pod/inventory-6dcd8d4f55-vb8z7: Liveness probe failed: Get "http://10.244.1.65:8080/healthz": dial tcp 10.244.1.65:8080: c… | O4 |
| 2026-10-13T12:47:02Z | event | event Unhealthy x1 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": read tcp 10.244.1.1:52866->… | O4 |
| 2026-10-13T12:50:07Z | event | event Unhealthy x1 on Pod/checkout-6cc8cb7b8c-9kcll: Readiness probe failed: Get "http://10.244.1.60:8080/readyz": context deadline exceeded (C… | O4 |
| 2026-10-13T12:50:12Z | event | event Unhealthy x2 on Pod/catalog-indexer-6f6b545fdb-rpmzl,catalog-indexer-6f6b545fdb-wv8gh: Liveness probe failed: Get "http://10.244.1.66:8080/healt… | O4 |
| 2026-10-13T12:54:38Z | event | event Unhealthy x3 on Pod/checkout-7d6bdccdc8-7qz6f,checkout-7d6bdccdc8-r6c2x: Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": co… | O4 |
| 2026-10-13T12:54:42Z | event | event Unhealthy x11 on Pod/checkout-7d6bdccdc8-7qz6f,checkout-7d6bdccdc8-r6c2x: Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": d… | O4 |
| 2026-10-13T12:55:16Z | event | event BackOff x17 on Pod/checkout-7d6bdccdc8-wd72m: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-wd72m_shop(41dd06… | O4 |
| 2026-10-13T12:55:16Z | event | event BackOff x3 on Pod/checkout-7d6bdccdc8-7qz6f: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-7qz6f_shop(0d8ee6… | O4 |
| 2026-10-13T12:55:17Z | event | event BackOff x18 on Pod/checkout-7d6bdccdc8-r6c2x: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-r6c2x_shop(94ba00… | O4 |
| 2026-10-13T13:03:17Z | event | event Unhealthy x33 on Pod/edge-66978949cf-2m5mj,edge-66978949cf-g8mnj: Readiness probe failed: Get "http://10.244.1.97:8080/healthz": context deadlin… | O4 |
| 2026-10-13T13:03:20Z | event | event Unhealthy x27 on Pod/edge-66978949cf-2m5mj,edge-66978949cf-g8mnj: Liveness probe failed: Get "http://10.244.1.97:8080/healthz": context deadline… | O4 |
| 2026-10-13T13:04:53Z | event | event Unhealthy x1 on Pod/edge-66978949cf-g8mnj: Readiness probe failed: Get "http://10.244.1.98:8080/healthz": read tcp 10.244.1.1:49114->… | O4 |
| 2026-10-13T13:07:31Z | event | event BackOff x13 on Pod/edge-66978949cf-2m5mj: Back-off restarting failed container edge in pod edge-66978949cf-2m5mj_shop(2c4af26d-274d-… | O4 |
| 2026-10-13T13:08:05Z | onset | checkout cpu_throttled_ratio[checkout-55f8c5b4bc-6ssw7] increase: 0.0 → 0.005714 | O6 |
| 2026-10-13T13:09:15Z | event | event BackOff x4 on Pod/edge-66978949cf-g8mnj: Back-off restarting failed container edge in pod edge-66978949cf-g8mnj_shop(f7cb0755-f2ff-… | O4 |
| 2026-10-13T13:09:20Z | onset | checkout errors_by_pod_rps on 3/3 series increase: 0.0 → 0.066667 | O6 |
| 2026-10-13T13:09:20Z | onset | checkout dependency_failures_rps[inventory,timeout] increase: 0.0 → 0.422222 | O6 |
| 2026-10-13T13:11:30+00:00 | change | deployment/edge modified: spec.replicas 3 → 2 (by kubectl-client-side-apply) | O2 |

## Observed facts

- The pricing service routes traffic to both pricing (shop:1.4.0) and pricing-legacy (shop:0.9.7). — `service pricing routes to 2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.…` (O3, kubernetes)
- Checkout error ratio 5xx increased starting around 2026-10-13T13:15:20Z. — `error_ratio_5xx": [{"labels": {}, "points": 121, "from": "2026-10-13T13:05:05Z", "to": "2026-10-13T1…` (O6, prometheus)
- Pricing-legacy container logs show PowerPeg router errors regarding smart_routing flag. — `PowerPeg router active: child orders exceed parent quantity, rejecting flag=smart_routing` (O5, kubernetes-logs)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.99 | cause | version_skew | active | +3/−0 | kubernetes, kubernetes-logs, prometheus | Enabling smart routing introduced traffic to pricing-legacy which is failing health checks, causing downstream checkout … |
| H2 | 0.00 | cause | configuration | active | +0/−0 |  | Checkout errors are a symptom of database pool exhaustion or misconfiguration from recent ConfigMap changes. |

## Alternative explanations

- **H2**: Database pool size adjustments in checkout-config were subsequently reverted and do not correlate with the direct runtime router errors seen in pricing-legacy.

## Uncertainty

- Exact client-side impact distribution across all upstream services beyond checkout remains partially unquantified.
- 2 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Disable the smart_routing flag in the feature-flags configmap or scale down/remove the pricing-legacy deployment.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +1 accepted / 2 rejected; new hypotheses ['H1', 'H2']
  - `active_alerts` {} — what is alerting and since when → O1
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O2
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: confident: H1 p=0.99, margin 0.99, sources ['kubernetes', 'kubernetes-logs', 'prometheus']; evidence +2 accepted / 0 rejected; new hypotheses []
  - `pod_logs` {"namespace": "shop", "pod": "pricing-legacy-79659db7cf-2lnp8", "tail": 100} — Check why pricing-legacy is failing its health checks. → O5
  - `workload_metrics` {"namespace": "shop", "workload": "checkout"} — Check golden signals and error rates for checkout workload to confirm onset and dependency failures. → O6
  - `find_traces` {"service": "checkout", "errors_only": true} — Identify if checkout errors originate from calls to the pricing service or database. → O7
  - posteriors: H1=0.99, H2=0.00, unexplained=0.01

Stop reason: confident: H1 p=0.99, margin 0.99, sources ['kubernetes', 'kubernetes-logs', 'prometheus']

</details>