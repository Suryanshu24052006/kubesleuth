# Checkout Errors Due to Unhealthy Pricing-Legacy Service via Smart Routing Flag

**Incident:** Checkout errors jumped to roughly a third of requests a few minutes ago.  
**Namespace:** `shop` · **Investigation:** `20261014-085732-38665b` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 2 rounds, 9 tool calls, 153.7s

## Root cause

Enabling the smart_routing feature flag routed checkout traffic to the newly created pricing-legacy deployment, which runs an older image and fails readiness probes, causing checkout error rates to spike.

*Hypothesis H1 · component `configmap/feature-flags` · category `configuration`*

**Confidence: HIGH** (posterior 0.98). High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.

## Causal chain

1. Deployment of pricing-legacy and modification of the feature flags configmap to set smart_routing to true. (O3)
2. Traffic was directed to pricing-legacy, which encountered startup and readiness probe failures. (O2, O4)
3. The pricing-legacy service started throwing errors stating 'PowerPeg router active: child orders exceed parent quantity, rejecting flag=smart_routing'. (O5)
4. Checkout error rates increased as dependencies failed or returned errors. (O6)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O4 | kubernetes | strong (+2.3) | `service pricing routes to 2 different workloads (pricing, pricing-legacy) running images` | Shows pricing service routes to the newly created pricing-legacy workload running an older image. |
| ✅ O5 | kubernetes-logs | strong (+2.3) | `PowerPeg router active: child orders exceed parent quantity, rejecting flag=smart_routing` | Shows pricing-legacy is throwing active errors related to the smart_routing flag. |
| ✅ O8 | prometheus | weak (+0.5) | `rate(dependency_requests_total{namespace="shop"}[1m])` | Dependency metrics reflect active traffic flowing between checkout and pricing/inventory endpoints around the time smart routing was enabled… |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-14T07:49:52.298Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-14T07:53:30+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (since reverted) (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/inventory modified: spec.replicas 4 → 1 (since reverted) (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x72 on Pod/checkout-68fb58bcfd-92lpn,checkout-68fb58bcfd-jlw7x: Readiness probe failed: Get "http://10.244.1.50:8080/readyz": dial tcp… | O2 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x10 on Pod/edge-6675f7688f-btmm6,edge-6675f7688f-dtglc: Readiness probe failed: Get "http://10.244.1.56:8080/healthz": dial tcp 10.244… | O2 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x13 on Pod/catalog-indexer-6f6b545fdb-27c8g,catalog-indexer-6f6b545fdb-mmpx4: Readiness probe failed: Get "http://10.244.1.44:8080/hea… | O2 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x18 on Pod/inventory-6ffc77fd45-28b67,inventory-6ffc77fd45-5hvm2: Readiness probe failed: Get "http://10.244.1.27:8080/healthz": dial … | O2 |
| 2026-10-14T08:01:26+00:00 | change | service/telemetry-collector-v2 created (by kubectl-client-side-apply) | O3 |
| 2026-10-14T08:01:26Z | change | service/telemetry-collector deleted | O3 |
| 2026-10-14T08:12:26Z | change | service/telemetry-collector-v2 deleted | O3 |
| 2026-10-14T08:12:27+00:00 | change | service/telemetry-collector created (by kubectl-client-side-apply) | O3 |
| 2026-10-14T08:15:36Z | event | event Unhealthy x14 on Pod/inventory-6ffc77fd45-dvnzz: Readiness probe failed: Get "http://10.244.1.30:8080/healthz": context deadline exceeded (… | O2 |
| 2026-10-14T08:15:43Z | event | event Unhealthy x4 on Pod/inventory-6ffc77fd45-dvnzz: Liveness probe failed: Get "http://10.244.1.30:8080/healthz": context deadline exceeded (C… | O2 |
| 2026-10-14T08:18:54+00:00 | change | deployment/catalog-indexer modified: spec.replicas 1 → 3 (by kubectl-client-side-apply) | O3 |
| 2026-10-14T08:18:54+00:00 | change | deployment/inventory modified: spec.replicas 1 → 4 (by kubectl-client-side-apply) | O3 |
| 2026-10-14T08:22:12+00:00 | change | deployment/checkout modified: containers[checkout].livenessProbe {"failureThreshold": 3, "httpG… → {"failureThreshold": 1, "httpG… (since reverted) (b… | O3 |
| 2026-10-14T08:22:12+00:00 | change | rollout/checkout new-revision | O3 |
| 2026-10-14T08:23:18Z | event | event Unhealthy x3 on Pod/checkout-68fb58bcfd-92lpn,checkout-68fb58bcfd-jlw7x: Liveness probe failed: Get "http://10.244.1.50:8080/healthz?deep=1": co… | O2 |
| 2026-10-14T08:23:22Z | event | event Unhealthy x12 on Pod/checkout-68fb58bcfd-92lpn,checkout-68fb58bcfd-jlw7x: Liveness probe failed: Get "http://10.244.1.50:8080/healthz?deep=1": d… | O2 |
| 2026-10-14T08:23:55Z | event | event BackOff x3 on Pod/checkout-68fb58bcfd-92lpn: Back-off restarting failed container checkout in pod checkout-68fb58bcfd-92lpn_shop(a664d5… | O2 |
| 2026-10-14T08:23:55Z | event | event BackOff x3 on Pod/checkout-68fb58bcfd-jsmz4: Back-off restarting failed container checkout in pod checkout-68fb58bcfd-jsmz4_shop(f450fc… | O2 |
| 2026-10-14T08:23:56Z | event | event BackOff x3 on Pod/checkout-68fb58bcfd-jlw7x: Back-off restarting failed container checkout in pod checkout-68fb58bcfd-jlw7x_shop(153907… | O2 |
| 2026-10-14T08:26:47+00:00 | change | deployment/checkout modified: containers[checkout].livenessProbe {"failureThreshold": 1, "httpG… → {"failureThreshold": 3, "httpG… (by kubectl-client-… | O3 |
| 2026-10-14T08:29:52+00:00 | change | configmap/edge-waf-rules modified: data.rules.json {"rules": [ {"id": "sqli-uni… → {"rules": [ {"id": "sqli-uni… (since reverted) (by kubectl-client-s… | O3 |
| 2026-10-14T08:31:12Z | event | event Unhealthy x35 on Pod/edge-6675f7688f-dtglc,edge-6675f7688f-qfm4b: Liveness probe failed: Get "http://10.244.1.22:8080/healthz": context deadline… | O2 |
| 2026-10-14T08:31:13Z | event | event Unhealthy x51 on Pod/edge-6675f7688f-dtglc,edge-6675f7688f-qfm4b: Readiness probe failed: Get "http://10.244.1.22:8080/healthz": context deadlin… | O2 |
| 2026-10-14T08:31:48Z | event | event Unhealthy x1 on Pod/edge-6675f7688f-dtglc: Readiness probe failed: Get "http://10.244.1.22:8080/healthz": read tcp 10.244.1.1:40794->… | O2 |
| 2026-10-14T08:34:52Z | onset | checkout errors_by_pod_rps on 3/3 series increase: 0.0 → 0.066667 | O6 |
| 2026-10-14T08:34:52Z | onset | checkout dependency_failures_rps on 2/3 series increase: 0.0 → 0.377778 | O6 |
| 2026-10-14T08:35:07Z | onset | checkout cpu_throttled_ratio on 3/3 series increase: 0.0 → 0.004032 | O6 |

## Observed facts

- The pricing service routes to both pricing and pricing-legacy workloads running different image versions. — `service pricing routes to 2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.…` (O4, kubernetes)
- Pricing-legacy pod experienced readiness probe failures due to connection refused. — `Readiness probe failed: Get "http://10.244.1.63:8080/healthz": dial tcp 10.244.1.63:8080: connect: c…` (O2, kubernetes)
- pricing-legacy logs show frequent errors rejecting requests due to 'child orders exceed parent quantity' when smart_routing is active. — `PowerPeg router active: child orders exceed parent quantity, rejecting flag=smart_routing` (O5, kubernetes-logs)
- Dependency requests metrics show various outcome series between checkout and pricing/inventory/recommendations. — `rate(dependency_requests_total{namespace="shop"}[1m])` (O8, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.98 | cause | configuration | active | +3/−0 | kubernetes, kubernetes-logs, prometheus | The smart routing feature flag enabled routing to pricing-legacy which is misconfigured or unhealthy, causing checkout e… |
| H2 | 0.01 | symptom | dependency | active | +0/−0 |  | Checkout service is returning 5xx errors due to downstream pricing service failures. |

## Alternative explanations

- **H2**: H2 frames the issue merely as a generic pricing dependency failure, whereas concrete evidence points directly to the newly introduced pricing-legacy deployment and the smart_routing feature flag activation.

## Uncertainty

- Exact trace propagation between checkout and pricing-legacy could not be fully pulled due to trace filtering, but metrics and logs strongly confirm the correlation.
- 3 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Disable the smart_routing feature flag in the feature-flags configmap.
- Investigate and fix the errors and probe failures in the pricing-legacy deployment before re-enabling smart routing.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +1 accepted / 1 rejected; new hypotheses ['H1', 'H2']
  - `active_alerts` {} — what is alerting and since when → O1
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: continue; evidence +1 accepted / 2 rejected; new hypotheses []
  - `pod_logs` {"namespace": "shop", "pod": "pricing-legacy-79659db7cf-n2xt5", "tail": 100} — Examine pricing-legacy logs to see why its health check is failing and why it is refusing connections. → O5
  - `workload_metrics` {"namespace": "shop", "workload": "checkout"} — Check checkout golden signals, specifically 5xx ratio and dependency call failures around the time smart_routing was enabled. → O6
  - `find_traces` {"service": "checkout", "minutes": 15, "errors_only": true} — Identify where errors originate in checkout traces, verifying if pricing or pricing-legacy is the root cause. → O7
  - posteriors: H1=0.96, H2=0.01, unexplained=0.03

**Round 2** — decision: confident: H1 p=0.98, margin 0.98, sources ['kubernetes', 'kubernetes-logs', 'prometheus']; evidence +1 accepted / 0 rejected; new hypotheses []
  - `query_metrics` {"promql": "rate(dependency_requests_total{namespace=\"shop\"}[1m])"} — Check specific dependency error rates from checkout to pricing and pricing-legacy. → O8
  - `pod_logs` {"namespace": "shop", "pod": "checkout-69cf4467b9-7vdxz", "tail": 100} — Check checkout logs to see if calls to pricing are returning the PowerPeg or pricing-legacy errors. → O9
  - posteriors: H1=0.98, H2=0.01, unexplained=0.02

Stop reason: confident: H1 p=0.98, margin 0.98, sources ['kubernetes', 'kubernetes-logs', 'prometheus']

</details>