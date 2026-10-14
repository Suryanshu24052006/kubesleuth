# Edge Service Latency and 502 Error Spike Due to Checkout Service Unresponsiveness

**Incident:** The edge service latency and error rate spiked; customers report timeouts.  
**Namespace:** `shop` · **Investigation:** `20261014-083153-b6478d` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 1 rounds, 8 tool calls, 275.7s

## Root cause

The checkout service became unresponsive and dropped connections starting at 08:13Z, causing downstream ConnectTimeout errors and 502 responses in the edge service.

*Hypothesis H4 · component `checkout` · category `dependency`*

**Confidence: HIGH** (posterior 0.99). High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.

## Causal chain

1. Checkout service pods failed readiness and liveness health checks (Unhealthy events reporting connection failures to port 8080). (O2)
2. Edge service requests to checkout began failing with ConnectTimeout starting at 08:13:30Z. (O5, O6, O7)
3. Edge service p95 latency degraded to 8.0 seconds and 5xx error ratio spiked to over 9%, generating customer-facing timeouts and 502 Bad Gateway responses. (O6, O7)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O5 | kubernetes-logs | strong (+2.3) | `checkout call failed error=ConnectTimeout` | Edge pod logs explicitly report ConnectTimeout when calling the checkout service. |
| ✅ O6 | jaeger | strong (+2.3) | `"message": "ConnectTimeout: "` | Jaeger distributed traces show edge HTTP 502 errors originate from ConnectTimeout. |
| ✅ O7 | prometheus | strong (+2.3) | `"dep": "checkout", "outcome": "connect_error"` | Workload metrics confirm dependency failures to checkout started concurrently with the incident. |

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
| 2026-10-14T07:53:30+00:00 | change | rollout/recommendations new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/review-bot new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/telemetry-collector new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | service/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/loadgen last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x8 on Pod/edge-6675f7688f-dtglc,edge-6675f7688f-qfm4b: Readiness probe failed: Get "http://10.244.1.22:8080/healthz": dial tcp 10.244.… | O2 |
| 2026-10-14T07:53:33Z | event | event Unhealthy x68 on Pod/checkout-68fb58bcfd-92lpn,checkout-68fb58bcfd-jlw7x: Readiness probe failed: Get "http://10.244.1.50:8080/readyz": dial tcp… | O2 |
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

## Observed facts

- The edge service is experiencing extremely high CPU utilization (283%) and its HPA is at maximum replicas. — `"resource": "cpu", "utilization_pct": 283` (O4, kubernetes)
- A complex regex rule for XSS detection was added to the edge-waf-rules ConfigMap at 08:29:52Z. — `"id": "xss-inline-js-2019-07", "pattern": "(?:(?:\\\"|'|\\]|\\}|\\\\|\\d|(?:nan|infinity|true|false|…` (O3, kubernetes)
- Edge pods began failing liveness and readiness probes due to timeouts (context deadline exceeded) starting at 08:31:12Z. — `Liveness probe failed: Get "http://10.244.1.22:8080/healthz": context deadline exceeded` (O2, kubernetes)
- An inventory pod was OOMKilled (exit code 137) at 08:19:04Z. — `"reason": "Error", "exit_code": 137, "finished_at": "2026-10-14T08:19:04+00:00"` (O4, kubernetes)
- Checkout service experienced significant readiness probe failures and restarts between 08:23Z and 08:26Z. — `Readiness probe failed: Get "http://10.244.1.50:8080/readyz": dial tcp 10.244.1.50:8080: connect: co…` (O2, kubernetes)
- There were cluster-level container runtime issues (containerd.sock connection reset) around 07:53Z affecting postgres and other services. — `Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from server: read u…` (O2, kubernetes)
- Edge 5xx error ratio onset occurred at 08:13:30Z, preceding the WAF ConfigMap change at 08:29:52Z. — `"onset": {"time": "2026-10-14T08:13:30Z", "direction": "increase", "baseline": 0.0, "value_after": 0…` (O7, prometheus)
- Edge p95 latency increased from 0.42s to 8.0s starting at 08:15:45Z. — `"onset": {"time": "2026-10-14T08:15:45Z", "direction": "increase", "baseline": 0.417363, "value_afte…` (O7, prometheus)
- Edge observed dependency timeouts calling checkout with onset at 08:15:45Z. — `"dep": "checkout", "outcome": "timeout"` (O7, prometheus)
- Edge CPU core usage only spiked at 08:31:15Z, long after edge 5xx errors and latency spiked. — `"onset": {"time": "2026-10-14T08:31:15Z", "direction": "increase", "baseline": 0.033438, "value_afte…` (O7, prometheus)
- Edge logs show 83 checkout call ConnectTimeout errors. — `checkout call failed error=ConnectTimeout` (O5, kubernetes-logs)
- Jaeger traces show errors originating from ConnectTimeout when edge calls downstream. — `"message": "ConnectTimeout: "` (O6, jaeger)
- Inventory service error ratio has returned to 0.0 and shows no container restarts or OOMs. — `"error_ratio_5xx": [{"labels": {}, "points": 108, "from": "2026-10-14T08:03:00Z", "to": "2026-10-14T…` (O8, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H4 | 0.99 | cause | dependency | active | +3/−0 | jaeger, kubernetes-logs, prometheus | Checkout service outage or unresponsiveness is causing upstream edge timeouts and 502 errors. |
| H1 | 0.01 | cause | configuration | active | +3/−1 | kubernetes | The new XSS WAF rule is causing catastrophic backtracking and CPU exhaustion in the edge service. |
| H3 | 0.00 | cause | other | active | +1/−0 | kubernetes | Node-level container runtime instability is causing intermittent probe failures across multiple services. |
| H5 | 0.00 | cause | configuration | active | +0/−0 |  | Telemetry collector service recreation at 08:12:27Z caused checkout to hang on telemetry export. |
| H2 | 0.00 | cause | resource_exhaustion | active | +1/−1 | kubernetes | Inventory service resource exhaustion is causing cascading timeouts at the edge. |

## Alternative explanations

- **H1**: The edge-waf-rules ConfigMap change occurred at 08:29:52Z, more than 15 minutes after the edge error ratio and latency onset at 08:13:30Z.
- **H2**: Inventory service metrics maintained a 0% error ratio and stable request handling during the incident window.
- **H3**: CRI pod sandbox creation errors predated the incident onset and do not explain the specific checkout connection timeouts.
- **H5**: While telemetry-collector was recreated at 08:12:27Z immediately prior to checkout failing, direct checkout logs and telemetry middleware traces are needed to confirm it as the internal trigger.

<details><summary>Evidence for/against other hypotheses</summary>

- H1 supports (strong, O3/kubernetes): `"id": "xss-inline-js-2019-07", "pattern": "(?:(?:\\\"|'|\\]|\\}|\\\\|\\d|(?:nan|infinity|true|false|…` — The addition of a complex regex rule immediately preceded the edge CPU spike and probe failures.
- H1 supports (strong, O4/kubernetes): `"resource": "cpu", "utilization_pct": 283` — Extremely high CPU utilization is a classic symptom of catastrophic backtracking in regex processing.
- H1 supports (moderate, O2/kubernetes): `Liveness probe failed: Get "http://10.244.1.22:8080/healthz": context deadline exceeded` — CPU saturation prevents the application from responding to health checks within the timeout period.
- H2 supports (moderate, O4/kubernetes): `"reason": "Error", "exit_code": 137, "finished_at": "2026-10-14T08:19:04+00:00"` — Inventory OOMKilled events indicate resource pressure that could cause dependency failures.
- H3 supports (weak, O2/kubernetes): `Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from server` — Earlier CRI errors suggest potential underlying node instability, though they predate the current edge spike.
- H1 contradicts (strong, O7/prometheus): `"onset": {"time": "2026-10-14T08:13:30Z", "direction": "increase", "baseline": 0.0, "value_after": 0…` — The edge error ratio onset was at 08:13:30Z, more than 15 minutes before the WAF ConfigMap modification at 08:29:52Z. Th…
- H2 contradicts (strong, O8/prometheus): `"error_ratio_5xx": [{"labels": {}, "points": 108, "from": "2026-10-14T08:03:00Z", "to": "2026-10-14T…` — Inventory metrics show 0% error ratio and normal memory/restart status.

</details>

## Uncertainty

- Checkout pod internal logs and thread dumps are required to determine why checkout stopped accepting connections at 08:13Z (e.g., synchronous telemetry export blocking vs application deadlock).
- 1 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Investigate checkout pod runtime logs and restore checkout service availability.
- Implement circuit breaking and shorter connect timeouts on the edge service for calls to checkout to prevent cascading thread starvation.
- Review telemetry collector client configuration in checkout to ensure telemetry exports are asynchronous and non-blocking.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +5 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `active_alerts` {} — what is alerting and since when → O1
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: confident: H4 p=0.99, margin 0.98, sources ['jaeger', 'kubernetes-logs', 'prometheus']; evidence +5 accepted / 1 rejected; new hypotheses ['H4', 'H5']
  - `pod_logs` {"namespace": "shop", "pod": "edge-6675f7688f-dtglc"} — To look for WAF processing errors, regex timeouts, or high latency logs in the edge service. → O5
  - `find_traces` {"service": "edge", "errors_only": false} — To determine if latency is originating within the edge service (WAF) or from a downstream dependency like inventory. → O6
  - `workload_metrics` {"namespace": "shop", "workload": "edge"} — To confirm if the CPU spike correlates exactly with the WAF rule change at 08:29:52Z. → O7
  - `workload_metrics` {"namespace": "shop", "workload": "inventory"} — To check if the inventory service is currently experiencing high memory usage or restarts. → O8
  - posteriors: H1=0.01, H2=0.00, H3=0.00, H4=0.99, H5=0.00, unexplained=0.00

Stop reason: confident: H4 p=0.99, margin 0.98, sources ['jaeger', 'kubernetes-logs', 'prometheus']

</details>