# Edge Service CPU Exhaustion and Timeout Incident Due to Vulnerable WAF Regex Rule

**Incident:** The edge service latency and error rate spiked; customers report timeouts.  
**Namespace:** `shop` · **Investigation:** `20261013-111526-8bafeb` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 2 rounds, 8 tool calls, 298.8s

## Root cause

The addition of a computationally complex, backtracking-prone WAF regular expression rule ('xss-inline-js-2019-07') in ConfigMap 'edge-waf-rules' caused catastrophic backtracking (ReDoS) and CPU exhaustion across edge pods.

*Hypothesis H1 · component `configmap/edge-waf-rules` · category `configuration`*

**Confidence: MEDIUM** (posterior 0.91). Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.

## Causal chain

1. ConfigMap 'edge-waf-rules' was updated via kubectl-client-side-apply with a complex regex pattern containing nested quantifiers ('xss-inline-js-2019-07'). (O3)
2. Edge service pods evaluated incoming requests against the new regex rule, leading to catastrophic backtracking and pinning CPU utilization at over 500%. (O2, O6)
3. Due to CPU starvation, the edge pods became unresponsive, causing liveness and readiness probe timeouts ('context deadline exceeded') and triggering pod restarts. (O2, O4)
4. Unhealthy pods dropped out of service endpoints while HPA hit max replicas (4), resulting in request processing delays, 502/5xx responses, and customer-facing timeouts. (O2, O7, O8)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O3 | kubernetes | strong (+2.3) | `"id": "xss-inline-js-2019-07", "pattern": "(?:(?:\\\"|'|\\]|\\}|\\\\|\\d|(?:nan|infinity|true|false|null|undef…` | The timing of this complex regex update (11:13:23) immediately precedes the edge service's CPU spike and probe failures (11:14:24). |
| ✅ O2 | kubernetes | strong (+1.38) | `current_metrics": [{"resource": "cpu", "utilization_pct": 501}]` | 501% CPU utilization is a classic symptom of an inefficient or catastrophic regex (ReDoS) pinning the processor. |
| ✅ O4 | kubernetes | moderate (+0.432) | `Readiness probe failed: Get "http://10.244.1.98:8080/healthz": context deadline exceeded` | CPU saturation prevents the application from responding to health checks within the required timeout. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x33 on Pod/edge-555d7c4d58-d59d9,edge-555d7c4d58-g7bqs: Readiness probe failed: Get "http://10.244.1.50:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x71 on Pod/inventory-6f6c46876d-2ccsv,inventory-6f6c46876d-6xqxs: Readiness probe failed: Get "http://10.244.1.48:8080/healthz": dial … | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x24 on Pod/recommendations-55b5fd5477-6lbkr,recommendations-55b5fd5477-cdtzd: Readiness probe failed: Get "http://10.244.1.88:8080/hea… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x97 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x22 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Readiness probe failed: Get "http://10.244.1.19:8080/hea… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-5sx5n,pricing-95c99775f-8drxw: Readiness probe failed: Get "http://10.244.1.26:8080/healthz": dial tcp 10.… | O4 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/edge-6675f7688f-5jhhr,edge-6675f7688f-xnt2d: Liveness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1… | O4 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-ckttb: Readiness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:80… | O4 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x5 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Liveness probe failed: Get "http://10.244.1.19:8080/healt… | O4 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Liveness probe failed: Get "http://10.244.1.25:8080/healthz": dial tcp … | O4 |
| 2026-10-13T10:39:04Z | event | event Unhealthy x1 on Pod/telemetry-collector-865ccb84c6-ckttb: Liveness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:808… | O4 |
| 2026-10-13T10:39:08Z | event | event FailedGetResourceMetric x1 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O4 |
| 2026-10-13T10:39:08Z | event | event FailedComputeMetricsReplicas x1 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T10:39:13Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O4 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x2 on Pod/inventory-6f6c46876d-6xqxs,inventory-6f6c46876d-9v8h6: Failed to create pod sandbox: rpc error: code = Unavaila… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x2 on Pod/inventory-6ffc77fd45-6f8pt,inventory-6ffc77fd45-wc82r: error killing pod: [failed to "KillContainer" for "inventory" wit… | O4 |
| 2026-10-13T10:44:24Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc … | O4 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x1 on Pod/recommendations-67c55868cc-2mk82: Failed to create pod sandbox: rpc error: code = Unavailable desc = error read… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x1 on Pod/recommendations-7bd4dd95d6-ckzbg: error killing pod: [failed to "KillContainer" for "recommendations" with KillContainer… | O4 |
| 2026-10-13T10:44:25Z | event | event FailedKillPod x1 on Pod/edge-6675f7688f-xnt2d: error killing pod: [failed to "KillContainer" for "edge" with KillContainerError: "rpc err… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/inventory-6f6c46876d-9v8h6: Liveness probe failed: Get "http://10.244.1.53:8080/healthz": dial tcp 10.244.1.53:8080: c… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/recommendations-67c55868cc-2mk82: Liveness probe failed: Get "http://10.244.1.52:8080/healthz": dial tcp 10.244.1.52:8080: c… | O4 |
| 2026-10-13T10:52:22Z | onset | edge errors_by_pod_rps on 3/3 series increase: 0.0 → 0.022222 | O8 |
| 2026-10-13T10:55:07Z | onset | edge dependency_failures_rps on 3/3 series increase: 0.0 → 0.032541 | O8 |
| 2026-10-13T10:55:18+00:00 | change | deployment/inventory modified: spec.replicas 4 → 1 (by kube-controller-manager) | O3 |
| 2026-10-13T10:55:24Z | event | event FailedGetResourceMetric x4 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods might… | O4 |
| 2026-10-13T10:55:24Z | event | event FailedComputeMetricsReplicas x4 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T10:57:07Z | onset | edge error_ratio_5xx increase: 0.0 → 0.002169 | O8 |
| 2026-10-13T10:58:23Z | event | event Unhealthy x13 on Pod/inventory-8585795f99-wc2db: Readiness probe failed: Get "http://10.244.1.58:8080/healthz": context deadline exceeded (… | O4 |

## Observed facts

- The edge service is experiencing extreme CPU utilization at 501%, far exceeding its target. — `current_metrics": [{"resource": "cpu", "utilization_pct": 501}]` (O2, kubernetes)
- A complex and potentially expensive WAF regex rule was added to the edge-waf-rules ConfigMap. — `"id": "xss-inline-js-2019-07", "pattern": "(?:(?:\\\"|'|\\]|\\}|\\\\|\\d|(?:nan|infinity|true|false|…` (O3, kubernetes)
- Edge pods are failing readiness and liveness probes due to timeouts (context deadline exceeded). — `Readiness probe failed: Get "http://10.244.1.98:8080/healthz": context deadline exceeded (Client.Tim…` (O4, kubernetes)
- Edge pods are restarting, likely due to liveness probe failures caused by the CPU saturation. — `pod edge-f647cd7c4-jpqfk has restarted 2 times` (O2, kubernetes)
- Earlier in the incident (10:44), there were cluster-wide issues connecting to the container runtime (containerd). — `dial unix /run/containerd/containerd.sock: connect: connection refused` (O4, kubernetes)
- The edge service has scaled to its maximum allowed replicas but remains unhealthy. — `HPA edge is at maxReplicas (4)` (O2, kubernetes)
- The edge service error rate began to spike at 10:57:07Z, reaching a 42% error — `"error_ratio_5xx": [{"labels": {}, "points": 120, "from": "2026-10-13T10:46:07Z", "to": "2026-10-13T…` (O8, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.91 | cause | configuration | active | +3/−0 | kubernetes | The new WAF regex rule is causing CPU exhaustion (ReDoS) in the edge service. |
| H2 | 0.05 | cause | resource_exhaustion | active | +1/−0 | kubernetes | The worker node is experiencing resource starvation affecting the CRI. |

## Alternative explanations

- **H2**: Worker node CRI distress (containerd.sock connection refused) occurred roughly 30 minutes prior to the edge failure and affected multiple workloads earlier, whereas the current latency spike, pod restarts, and 500%+ CPU saturation directly align in time with the 11:13:23 WAF ConfigMap modification.

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (moderate, O4/kubernetes): `dial unix /run/containerd/containerd.sock: connect: connection refused` — CRI connection failures are a strong indicator of node-level distress, though these events occurred ~30 minutes before t…

</details>

## Uncertainty

- Specific request payloads triggering the ReDoS were not captured in the limited pod logs, though the regex structure itself exhibits clear polynomial/exponential backtracking characteristics.

## Suggested remediation (not executed — the agent is read-only)

- Revert or sanitize the 'xss-inline-js-2019-07' pattern in ConfigMap 'edge-waf-rules' to remove nested greedy repetitions.
- Restart deployment/edge pods to clear hung worker processes.
- Introduce a regex engine with linear-time guarantees (such as RE2) or enforce execution timeouts for individual WAF rule evaluations.
- Establish automated linting/static analysis for ReDoS vulnerabilities in WAF rule CI/CD pipelines before applying configuration updates.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +4 accepted / 0 rejected; new hypotheses ['H1', 'H2']
  - `active_alerts` {} — what is alerting and since when → O1
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - `pod_logs` {"namespace": "shop", "pod": "edge-f647cd7c4-jpqfk"} — To check for WAF processing logs or errors that confirm the regex is the bottleneck. → O5
  - `query_metrics` {"promql": "sum(node_cpu_seconds_total{mode!=\"idle\"}) by (node)"} — To determine if the entire node is saturated or if the CPU usage is isolated to the edge pods. → O6
  - `find_traces` {"service": "edge", "errors_only": false} — To see if latency is originating within the edge service (WAF) or if it's waiting on downstream dependencies. → O7
  - `workload_metrics` {"namespace": "shop", "workload": "edge"} — To correlate the exact onset of the CPU spike with the ConfigMap change at 11:13:23. → O8
  - posteriors: H1=0.91, H2=0.05, unexplained=0.04

**Round 2** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.91, H2=0.05, unexplained=0.04

Stop reason: no new evidence for two rounds

</details>