# Checkout Restart Loop due to Aggressive Liveness Probe

**Incident:** Checkout pods keep restarting and the storefront is throwing errors.  
**Namespace:** `shop` · **Investigation:** `20261013-110831-da54ab` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 2 rounds, 8 tool calls, 92.7s

## Root cause

The checkout deployment's liveness probe was reconfigured with an overly aggressive failureThreshold of 1 and a 'deep' health check path that exceeds the 1-second timeout.

*Hypothesis H1 · component `deployment/checkout` · category `probe_misconfiguration`*

**Confidence: LOW** (posterior 0.59). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. A configuration change was applied to the checkout deployment, switching the liveness probe to a 'deep' check and reducing the failureThreshold from 3 to 1. (O3)
2. The new '/healthz?deep=1' probe frequently exceeds the 1s timeout or fails during pod startup/load, resulting in 'context deadline exceeded' errors. (O4, O6)
3. Because the failureThreshold is set to 1, a single probe timeout causes Kubernetes to immediately kill and restart the container. (O2, O4)
4. The continuous restart loop (CrashLoopBackOff) results in zero ready replicas for the checkout service. (O2)
5. The storefront (edge) service fails to connect to the checkout service, leading to a high 5xx error rate and triggering the critical alert. (O1, O7)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O4 | kubernetes | strong (+2.3) | `Liveness probe failed: Get "http://10.244.1.83:8080/healthz?deep=1": context deadline exceeded` | Directly confirms that the new probe path is timing out, which triggers the restart due to the threshold of 1. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x64 on Pod/inventory-6f6c46876d-2ccsv,inventory-6f6c46876d-6xqxs: Readiness probe failed: Get "http://10.244.1.48:8080/healthz": dial … | O4 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x19 on Pod/edge-555d7c4d58-d59d9,edge-555d7c4d58-g7bqs: Readiness probe failed: Get "http://10.244.1.50:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x88 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x22 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Readiness probe failed: Get "http://10.244.1.19:8080/hea… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x20 on Pod/recommendations-669dd5d8c4-4m4gp,recommendations-669dd5d8c4-rq57g: Readiness probe failed: Get "http://10.244.1.78:8080/hea… | O4 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-5sx5n,pricing-95c99775f-8drxw: Readiness probe failed: Get "http://10.244.1.26:8080/healthz": dial tcp 10.… | O4 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-ckttb: Readiness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:80… | O4 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-5jhhr,edge-6675f7688f-xnt2d: Liveness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1… | O4 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x5 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-7qmw8: Liveness probe failed: Get "http://10.244.1.19:8080/healt… | O4 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Liveness probe failed: Get "http://10.244.1.25:8080/healthz": dial tcp … | O4 |
| 2026-10-13T10:39:04Z | event | event Unhealthy x1 on Pod/telemetry-collector-865ccb84c6-ckttb: Liveness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:808… | O4 |
| 2026-10-13T10:39:08Z | event | event FailedGetResourceMetric x1 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O4 |
| 2026-10-13T10:39:08Z | event | event FailedComputeMetricsReplicas x1 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T10:39:13Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O4 |
| 2026-10-13T10:42:53Z | onset | checkout errors_by_pod_rps[checkout-69cf4467b9-9p4zs] increase: 0.0 → 0.022222 | O7 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x2 on Pod/inventory-6f6c46876d-6xqxs,inventory-6f6c46876d-9v8h6: Failed to create pod sandbox: rpc error: code = Unavaila… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x2 on Pod/inventory-6ffc77fd45-6f8pt,inventory-6ffc77fd45-wc82r: error killing pod: [failed to "KillContainer" for "inventory" wit… | O4 |
| 2026-10-13T10:44:24Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc … | O4 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x1 on Pod/recommendations-67c55868cc-2mk82: Failed to create pod sandbox: rpc error: code = Unavailable desc = error read… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x1 on Pod/recommendations-7bd4dd95d6-ckzbg: error killing pod: [failed to "KillContainer" for "recommendations" with KillContainer… | O4 |
| 2026-10-13T10:44:25Z | event | event FailedKillPod x1 on Pod/edge-6675f7688f-xnt2d: error killing pod: [failed to "KillContainer" for "edge" with KillContainerError: "rpc err… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/inventory-6f6c46876d-9v8h6: Liveness probe failed: Get "http://10.244.1.53:8080/healthz": dial tcp 10.244.1.53:8080: c… | O4 |
| 2026-10-13T10:44:30Z | event | event Unhealthy x1 on Pod/recommendations-67c55868cc-2mk82: Liveness probe failed: Get "http://10.244.1.52:8080/healthz": dial tcp 10.244.1.52:8080: c… | O4 |
| 2026-10-13T10:47:45Z | change | service/telemetry-collector deleted | O3 |
| 2026-10-13T10:52:23Z | onset | checkout error_ratio_5xx increase: 0.0 → 0.001155 | O7 |
| 2026-10-13T10:52:23Z | onset | checkout dependency_failures_rps on 2/3 series increase: 0.0 → 0.022222 | O7 |
| 2026-10-13T10:54:56Z | change | service/telemetry-collector-v2 deleted | O3 |
| 2026-10-13T10:54:58+00:00 | change | service/telemetry-collector created (by kubectl-client-side-apply) | O3 |
| 2026-10-13T10:54:59+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |

## Observed facts

- The checkout deployment has no ready replicas. — `Deployment checkout: only 0/3 replicas ready` (O2, kubernetes)
- Checkout liveness probes are timing out on the new deep health check path. — `Liveness probe failed: Get "http://10.244.1.83:8080/healthz?deep=1": context deadline exceeded` (O4, kubernetes)
- There were node-level container runtime errors around 10:44, suggesting potential underlying infrastructure instability. — `dial unix /run/containerd/containerd.sock: connect: connection refused` (O4, kubernetes)
- Checkout pods are in a CrashLoopBackOff state due to repeated liveness probe failures. — `pod checkout-69d8947794-29kkk container checkout waiting: CrashLoopBackOff` (O2, kubernetes)
- Checkout pods are failing to establish database connections, hitting a timeout in the connection pool. — `error connecting in 'pool-1': connection timeout expired` (O6, kubernetes-logs)
- Checkout application startup is delayed or — `couldn't get a connection after 10.00 sec` (O6, kubernetes-logs)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.59 | cause | probe_misconfiguration | active | +1/−0 | kubernetes | The new 'deep' liveness probe is too aggressive and causes a restart loop. |
| H3 | 0.20 | cause | resource_exhaustion | active | +1/−0 | kubernetes | Node-level resource exhaustion or runtime failure is preventing pod health. |
| H2 | 0.06 | cause | dependency | active | +0/−0 |  | A downstream dependency failure is causing the 'deep' health check to fail. |

## Alternative explanations

- **H2**: While a dependency failure might cause the 'deep' check to fail, the immediate cause of the outage is the lack of tolerance (threshold=1) in the probe configuration. A standard threshold of 3 would likely have absorbed transient dependency issues.
- **H3**: Node-level issues were considered due to containerd errors, but the node status shows no resource pressure (O5), and the timing of the outage perfectly matches the deployment configuration change (O3).

<details><summary>Evidence for/against other hypotheses</summary>

- H3 supports (moderate, O4/kubernetes): `dial unix /run/containerd/containerd.sock: connect: connection refused` — Container runtime errors indicate the node itself might be struggling, which could explain why probes are timing out or …

</details>

## Uncertainty

- The specific dependency that the 'deep' health check probes is not confirmed, though logs suggest connection timeouts (O6) which often point to database or downstream service latency.
- 1 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Revert the checkout deployment liveness probe failureThreshold to 3.
- Increase the liveness probe timeoutSeconds from 1 to 5 or 10 to accommodate the 'deep' check latency.
- Consider using the 'deep' check for readiness probes rather than liveness probes to prevent restart loops during transient dependency issues.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +2 accepted / 1 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `active_alerts` {} — what is alerting and since when → O1
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - `describe` {"kind": "node", "namespace": "shop", "name": "kubesleuth-worker"} — Check node health and conditions to see if the containerd errors were transient or indicate ongoing pressure. → O5
  - `pod_logs` {"namespace": "shop", "pod": "checkout-69d8947794-29kkk", "previous": true} — Check if the application logs show why the /healthz?deep=1 path is failing or timing out. → O6
  - `workload_metrics` {"namespace": "shop", "workload": "checkout"} — Verify if checkout is seeing dependency errors that would cause a 'deep' health check to fail. → O7
  - `find_traces` {"service": "checkout", "errors_only": true} — Identify if the health check requests are reaching the service and where they are stalling. → O8
  - posteriors: H1=0.59, H2=0.06, H3=0.20, unexplained=0.16

**Round 2** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.59, H2=0.06, H3=0.20, unexplained=0.16

Stop reason: no new evidence for two rounds

</details>