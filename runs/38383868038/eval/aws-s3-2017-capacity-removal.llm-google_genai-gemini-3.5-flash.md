# Node-level CRI failure on kubesleuth-worker causing widespread service timeouts

**Incident:** Checkout requests are timing out and the edge is returning 5xx.  
**Namespace:** `shop` · **Investigation:** `20261013-105949-8346bc` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 2 rounds, 8 tool calls, 121.3s

## Root cause

The container runtime (containerd) on node 'kubesleuth-worker' became unresponsive or crashed, preventing the Kubelet from performing health probes and managing container lifecycles.

*Hypothesis H1 · component `node/kubesleuth-worker` · category `resource_exhaustion`*

**Confidence: LOW** (posterior 0.59). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. The container runtime on node 'kubesleuth-worker' began refusing connections on its Unix socket. (O2)
2. Kubelet failed to execute readiness and liveness probes for multiple pods (inventory, edge, catalog-indexer) residing on the affected node. (O2)
3. Simultaneously, the inventory service was scaled down from 4 to 1 replicas, concentrating traffic on a single pod that was already failing probes or resource-constrained. (O4, O7)
4. The remaining inventory pod experienced OOMKill (exit code 137) and high CPU throttling, leading to 8-second latencies. (O3, O7)
5. The checkout service timed out waiting for inventory responses, causing the edge gateway to return 5xx errors to users. (O1, O6)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O2 | kubernetes | strong (+2.3) | `dial unix /run/containerd/containerd.sock: connect: connection refused` | Direct evidence of the container runtime being unreachable, which explains why probes are failing across unrelated pods. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:38:53+00:00 | change | rollout/telemetry-collector new-revision | O4 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x41 on Pod/inventory-6f6c46876d-2ccsv,inventory-6f6c46876d-6xqxs: Readiness probe failed: Get "http://10.244.1.48:8080/healthz": dial … | O2 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x13 on Pod/edge-555d7c4d58-d59d9,edge-555d7c4d58-g7bqs: Readiness probe failed: Get "http://10.244.1.50:8080/healthz": dial tcp 10.244… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x13 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-mtscn: Readiness probe failed: Get "http://10.244.1.19:8080/hea… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x16 on Pod/recommendations-67c55868cc-2mk82,recommendations-67c55868cc-5f6w2: Readiness probe failed: Get "http://10.244.1.52:8080/hea… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x29 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp… | O2 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-5sx5n,pricing-95c99775f-8drxw: Readiness probe failed: Get "http://10.244.1.26:8080/healthz": dial tcp 10.… | O2 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-ckttb: Readiness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:80… | O2 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-5jhhr,edge-6675f7688f-xnt2d: Liveness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1… | O2 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x3 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-mtscn: Liveness probe failed: Get "http://10.244.1.19:8080/healt… | O2 |
| 2026-10-13T10:39:03Z | event | event Unhealthy x3 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Liveness probe failed: Get "http://10.244.1.25:8080/healthz": dial tcp … | O2 |
| 2026-10-13T10:39:04Z | event | event Unhealthy x1 on Pod/telemetry-collector-865ccb84c6-ckttb: Liveness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:808… | O2 |
| 2026-10-13T10:39:08Z | event | event FailedGetResourceMetric x1 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O2 |
| 2026-10-13T10:39:08Z | event | event FailedComputeMetricsReplicas x1 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O2 |
| 2026-10-13T10:39:09+00:00 | change | deployment/catalog-indexer modified: spec.replicas 3 → 1 (by kube-controller-manager) | O4 |
| 2026-10-13T10:39:13Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe failed: /var/run/postgresql:5432 - no response | O2 |
| 2026-10-13T10:39:19+00:00 | change | statefulset/postgres last-write (by kube-controller-manager) | O4 |
| 2026-10-13T10:44:11+00:00 | change | deployment/checkout modified: template.annotations null → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O4 |
| 2026-10-13T10:44:11+00:00 | change | deployment/edge modified: template.annotations null → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O4 |
| 2026-10-13T10:44:11+00:00 | change | deployment/recommendations modified: template.annotations null → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O4 |
| 2026-10-13T10:44:11+00:00 | change | deployment/inventory modified: template.annotations null → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O4 |
| 2026-10-13T10:44:11+00:00 | change | rollout/checkout new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T10:44:11+00:00 | change | rollout/edge new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T10:44:11+00:00 | change | rollout/inventory new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T10:44:11+00:00 | change | rollout/recommendations new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O4 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x2 on Pod/inventory-6f6c46876d-6xqxs,inventory-6f6c46876d-9v8h6: Failed to create pod sandbox: rpc error: code = Unavaila… | O2 |
| 2026-10-13T10:44:24Z | event | event FailedKillPod x2 on Pod/inventory-6ffc77fd45-6f8pt,inventory-6ffc77fd45-wc82r: error killing pod: [failed to "KillContainer" for "inventory" wit… | O2 |
| 2026-10-13T10:44:24Z | event | event Unhealthy x1 on Pod/postgres-0: Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc … | O2 |
| 2026-10-13T10:44:24Z | event | event FailedCreatePodSandBox x1 on Pod/recommendations-67c55868cc-2mk82: Failed to create pod sandbox: rpc error: code = Unavailable desc = error read… | O2 |

## Observed facts

- The edge service is experiencing a critical failure rate, with over 70% of requests returning 5xx errors. — `73.06% of edge requests fail with 5xx.` (O1, alertmanager)
- Multiple pods reported failures communicating with the container runtime (containerd) on the node. — `dial unix /run/containerd/containerd.sock: connect: connection refused` (O2, kubernetes)
- The only remaining inventory pod was terminated with exit code 137 (SIGKILL), likely due to OOM or node pressure. — `last_termination": {"container": "inventory", "reason": "Error", "exit_code": 137, "finished_at": "2…` (O3, kubernetes)
- The inventory pod is failing readiness and liveness probes due to timeouts. — `Readiness probe failed: Get "http://10.244.1.58:8080/healthz": context deadline exceeded` (O2, kubernetes)
- The HPA for the edge service is failing to retrieve metrics because pods are in an unready state. — `failed to get cpu utilization: did not receive metrics for targeted pods (pods might be unready)` (O2, kubernetes)
- The node kubesleuth-worker is healthy with no memory, disk, or PID pressure. — `"status": {"conditions": [{"type": "MemoryPressure", "status": "False", "reason": "KubeletHasSuffici…` (O5, kubernetes)
-  — `connection failed: connection to server at \"10.96.8` (O6, kubernetes-logs)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.59 | cause | resource_exhaustion | active | +1/−0 | kubernetes | Node-level resource exhaustion or CRI failure on kubesleuth-worker. |
| H2 | 0.20 | cause | capacity | active | +1/−0 | kubernetes | Inventory service bottleneck due to scale-down and resource limits. |
| H3 | 0.06 | cause | dependency | active | +0/−0 |  | Telemetry collector dependency failure after service renaming. |

## Alternative explanations

- **H2**: While the inventory scale-down and OOMKill certainly contributed to the failure, they do not explain the 'connection refused' errors to the containerd socket or the simultaneous probe failures across unrelated services like catalog-indexer.
- **H3**: Telemetry service changes occurred in the same window, but there is no direct evidence in logs or traces that services were blocking on telemetry exports; the CRI failure is a more fundamental explanation for the observed symptoms.

<details><summary>Evidence for/against other hypotheses</summary>

- H2 supports (moderate, O3/kubernetes): `last_termination": {"container": "inventory", "reason": "Error", "exit_code": 137` — Exit code 137 often indicates an OOMKill, suggesting the single replica could not handle the load.

</details>

## Uncertainty

- The specific trigger for the containerd failure (e.g., PID exhaustion, disk I/O hang, or a kernel bug) is unknown. Node-level system logs (journalctl) would be required to confirm the exact cause of the runtime crash.
- 2 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Restart the containerd service on node 'kubesleuth-worker' or reboot the node.
- Scale the inventory deployment back to its original replica count (4) to alleviate pressure on the single remaining pod.
- Investigate node-level metrics for PID or Disk pressure that might have led to the CRI failure.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +2 accepted / 2 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `active_alerts` {} — what is alerting and since when → O1
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O3
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O4

**Round 1** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - `describe` {"kind": "node", "namespace": "shop", "name": "kubesleuth-worker"} — To check for node-level pressures or runtime status that would explain the containerd connection errors. → O5
  - `pod_logs` {"namespace": "shop", "pod": "inventory-8585795f99-wc2db", "previous": true} — To see the logs of the inventory pod before it was killed (exit code 137) to check for OOM or startup errors. → O6
  - `workload_metrics` {"namespace": "shop", "workload": "inventory"} — To check if the inventory service was saturated (CPU/Memory) after the scale-down. → O7
  - `find_traces` {"service": "checkout", "minutes": 15} — To determine if checkout timeouts are caused by a specific downstream dependency like inventory. → O8
  - posteriors: H1=0.59, H2=0.20, H3=0.06, unexplained=0.16

**Round 2** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.59, H2=0.20, H3=0.06, unexplained=0.16

Stop reason: no new evidence for two rounds

</details>