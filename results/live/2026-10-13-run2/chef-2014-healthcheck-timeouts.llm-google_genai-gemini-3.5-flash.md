# Checkout Service CrashLoop Due to Misconfigured Liveness Probe

**Incident:** Checkout pods keep restarting and the storefront is throwing errors.  
**Namespace:** `shop` · **Investigation:** `20261013-125637-4cc8b4` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 1 rounds, 6 tool calls, 169.8s

## Root cause

A patch applied to the checkout deployment modified the liveness probe path to '/healthz?deep=1' with an overly aggressive failure threshold of 1, causing containers to be repeatedly killed when deep health checks fail or time out.

*Hypothesis H1 · component `deployment/checkout` · category `probe_misconfiguration`*

**Confidence: HIGH** (posterior 0.96). High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.

## Causal chain

1. At 12:53:21 UTC, a patch modified the checkout deployment liveness probe path to '/healthz?deep=1' with a failure threshold of 1. (O3, O5)
2. The checkout application containers failed the new liveness probe due to deep check errors and strict timeout/failure constraints, leading to container termination. (O2, O4, O6)
3. All checkout pods entered CrashLoopBackOff with 0/3 replicas ready, disrupting downstream dependencies and triggering the storefront high 5xx error alert. (O1, O2)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O3 | kubernetes | strong (+2.3) | `{"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=1", "port": "http", "scheme": "HTTP"}, "periodSecon…` | Directly demonstrates the liveness probe change that immediately preceded the checkout pod crashes. |
| ✅ O4 | kubernetes | strong (+1.38) | `Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": dial tcp 10.244.1.82:8080: connect: conne…` | Shows direct evidence of liveness probe failures on the newly configured /healthz?deep=1 endpoint. |
| ✅ O5 | kubernetes | strong (+0.828) | `"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=1"` | The deployment describe output confirms the liveness probe was modified to path '/healthz?deep=1' with a strict failureThreshold of 1. |
| ✅ O6 | kubernetes-logs | moderate (+1.2) | `error connecting in 'pool-1': connection timeout expired` | Container logs show database connection timeouts occurring during startup, explaining why deep health checks or general responses might fail… |

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
| 2026-10-13T12:29:51+00:00 | change | service/telemetry-collector-v2 created (by kubectl-client-side-apply) | O3 |
| 2026-10-13T12:29:51Z | change | service/telemetry-collector deleted | O3 |
| 2026-10-13T12:42:34Z | change | service/telemetry-collector-v2 deleted | O3 |
| 2026-10-13T12:42:35+00:00 | change | service/telemetry-collector created (by kubectl-client-side-apply) | O3 |
| 2026-10-13T12:42:36+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-roll… | O3 |
| 2026-10-13T12:42:36+00:00 | change | deployment/edge modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-rollout) | O3 |

## Observed facts

- The liveness probe configuration for checkout was modified at 2026-10-13T12:53:21+00:00 to failureThreshold: 1 and path: /healthz?deep=1. — `containers[checkout].livenessProbe` (O3, kubernetes)
- Checkout pods are experiencing liveness probe failures due to connection refused on /healthz?deep=1. — `Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": dial tcp 10.244.1.82:8080: conn…` (O4, kubernetes)
- All checkout pods are currently in CrashLoopBackOff with 0/3 replicas ready. — `pod checkout-7d6bdccdc8-7qz6f container checkout waiting: CrashLoopBackOff` (O2, kubernetes)
- ShopEdgeHigh5xxRate alert is firing, indicating 61.56% of edge requests fail with 5xx. — `Edge is returning >5% 5xx responses` (O1, alertmanager)
- The liveness probe for the checkout container was updated to query '/healthz?deep=1' with failureThreshold: 1 and timeoutSeconds: 1. — `"livenessProbe": {"failureThreshold": 1, "httpGet": {"path": "/healthz?deep=1", "port": "http", "sch…` (O5, kubernetes)
- Previous container logs for checkout show database pool connection timeouts during startup/operation. — `error connecting in 'pool-1': connection timeout expired` (O6, kubernetes-logs)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.96 | cause | probe_misconfiguration | active | +4/−0 | kubernetes, kubernetes-logs | The checkout liveness probe path '/healthz?deep=1' or tight failure threshold (1) is failing or not supported by the app… |
| H3 | 0.00 | cause | dependency | active | +0/−0 |  | Database connectivity issues or downstream database exhaustion prevents the checkout service from starting or responding… |
| H2 | 0.03 | symptom | dependency | active | +1/−0 | kubernetes | Edge is returning 5xx responses as a symptom because the upstream checkout service has 0 ready endpoints and is crashing… |

## Alternative explanations

- **H2**: Edge 5xx errors are merely a symptom caused by the complete unavailability of the upstream checkout service rather than an independent failure in the edge service itself.
- **H3**: While database connection timeouts appear in container logs, the timing and direct correlation with the liveness probe patch modification at 12:53:21 UTC point decisively to probe misconfiguration as the root cause of the continuous restarts.

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (strong, O2/kubernetes): `service checkout has 0 ready endpoints (3 not ready)` — Confirms the checkout dependency is completely unavailable, explaining the edge 5xx errors.

</details>

## Uncertainty

- Whether the application code natively supports the '/healthz?deep=1' query parameter or if it inherently times out under normal database connection latency.
- 1 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Revert the checkout liveness probe configuration back to its original path ('/healthz') and restore the failureThreshold to 3.
- Verify that the checkout application can successfully connect to PostgreSQL without connection timeouts during startup.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +3 accepted / 0 rejected; new hypotheses ['H1', 'H2']
  - `active_alerts` {} — what is alerting and since when → O1
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: confident: H1 p=0.96, margin 0.95, sources ['kubernetes', 'kubernetes-logs']; evidence +2 accepted / 1 rejected; new hypotheses ['H3']
  - `describe` {"kind": "deployment", "namespace": "shop", "name": "checkout"} — Inspect the full deployment specification for checkout to verify the exact probe parameters currently active. → O5
  - `pod_logs` {"namespace": "shop", "pod": "checkout-7d6bdccdc8-7qz6f", "previous": true} — Check the previous logs of a crashed checkout pod to see if the application logs indicate why /healthz?deep=1 failed or if it was abruptly killed. → O6
  - posteriors: H1=0.96, H2=0.03, H3=0.00, unexplained=0.01

Stop reason: confident: H1 p=0.96, margin 0.95, sources ['kubernetes', 'kubernetes-logs']

</details>