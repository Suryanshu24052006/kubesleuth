# Checkout 502s and Recommendations Instability during Bulk Rollout

**Incident:** Checkout is intermittently failing with 502s; recommendations pods are restarting.  
**Namespace:** `shop` · **Investigation:** `20261014-080458-851d1d` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 4 rounds, 19 tool calls, 447.9s

## Root cause

A simultaneous rollout of all services in the 'shop' namespace triggered transient node-level resource exhaustion and containerd socket saturation on the 'kubesleuth-worker' node.

*Hypothesis H2 · component `node/kubesleuth-worker` · category `resource_exhaustion`*

**Confidence: HIGH** (posterior 0.90). High: the leading cause is supported by multiple independent sources and nothing strongly contradicts it.

## Causal chain

1. Bulk rollout of all deployments, statefulsets, and services at 07:53:30Z. (O3)
2. The burst of container creations and image pulls overwhelmed the container runtime (containerd) on the worker node, leading to socket connection errors. (O2, O14)
3. Postgres-0 failed readiness probes and experienced ImageInspectErrors due to the runtime saturation, making the database temporarily unavailable. (O2, O14)
4. The checkout service failed to connect to the database, resulting in 502 errors at the edge. (O5)
5. Recommendations pods experienced high CPU throttling and readiness probe failures during the startup period due to node-level resource contention. (O19, O14)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O2 | kubernetes | strong (+2.3) | `dial unix /run/containerd/containerd.sock: connect: connection refused` | Containerd socket errors during a massive rollout strongly suggest node-level infrastructure strain. |
| ✅ O11 | kubernetes | moderate (+0.72) | `"lastTransitionTime": "2026-10-14T07:53:46+00:00", "status": "True", "type": "PodReadyToStartContainers"` | The delay between pod creation (07:53:30) and container start (07:53:49) is consistent with node-level pressure or image pull delays during … |
| ✅ O14 | kubernetes | strong (+0.828) | `dial unix /run/containerd/containerd.sock: connect: connection refused` | Direct evidence of container runtime saturation/failure during the burst of rollouts. |
| ✅ O19 | prometheus | moderate (+1.2) | `"cpu_throttled_ratio": [{"labels": {"pod": "recommendations-7bd4dd95d6-pxghg"}, "points": 73, "from": "2026-10…` | The spike in CPU throttling during the rollout period suggests node-level resource contention or kubelet/containerd saturation. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-14T07:49:52.298Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-14T07:53:29+00:00 | change | configmap/checkout-config last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | configmap/edge-waf-rules last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | configmap/feature-flags last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | configmap/kube-root-ca.crt last-write (by kube-controller-manager) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/catalog-indexer last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/checkout last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/edge last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/inventory last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/postgres last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:29+00:00 | change | service/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/catalog-indexer new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/checkout new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/edge new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/inventory new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/loadgen new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/pricing new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/recommendations new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/review-bot new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | rollout/telemetry-collector new-revision | O3 |
| 2026-10-14T07:53:30+00:00 | change | service/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/catalog-indexer last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/checkout last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/edge last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/inventory last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/loadgen last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/pricing last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/recommendations last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/review-bot last-write (by kubectl-client-side-apply) | O3 |
| 2026-10-14T07:53:30+00:00 | change | deployment/telemetry-collector last-write (by kubectl-client-side-apply) | O3 |

## Observed facts

- Widespread readiness probe failures occurred across multiple services immediately following the rollout. — `Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp 10.244.1.25:8080: connect: co…` (O2, kubernetes)
- The postgres pod failed to start initially due to containerd socket connection errors. — `Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from server: read u…` (O2, kubernetes)
- The HPA for the edge service failed to retrieve metrics during the incident window. — `failed to get cpu utilization: unable to get metrics for resource cpu: no metrics returned from reso…` (O2, kubernetes)
- Current pods are all reported as Ready with 0 restarts, despite the incident report of restarts. — `ready: 1/1, restarts: 0, node: kubesleuth-worker, image: docker.io/library/shop:1.4.0, age: 11m` (O4, kubernetes)
- Checkout pods were unable to connect to the Postgres database immediately following the rollout. — `connection to server at "10.96.36.109", port 5432 failed: Connection refused` (O5, kubernetes-logs)
- The postgres-0 pod is currently in the Running phase. — `"status": {"phase": "Running"` (O11, kubernetes)
- The postgres container in postgres-0 is reported as ready. — `"ready": true` (O11, kubernetes)
- Postgres is configured with a low maximum connection limit of 40. — `"args": ["-c", "max_connections=40", "-c", "log_connections=off"]` (O11, kubernetes)
- The recommendations deployment reports all replicas are available and ready. — `"availableReplicas": 2, "observedGeneration": 1, "readyReplicas": 2` (O12, kubernetes)
- Recommendations pods are configured to send telemetry to a service named 'telemetry-collector'. — `{"name": "TELEMETRY_URL", "value": "http://telemetry-collector:8080/ingest"}` (O12, kubernetes)
- The container runtime (containerd) on the worker node was unresponsive during the rollout, causing image inspection and sandbox creation failures. — `dial unix /run/containerd/containerd.sock: connect: connection refused` (O14, kubernetes)
- Multiple services (checkout, catalog-indexer, edge, inventory, pricing, recommendations) experienced simultaneous readiness probe failures immediately after the rollout. — `Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp 10.244.1.25:8080: connect: co…` (O14, kubernetes)
- Postgres successfully recovered from the initial container runtime errors and was ready to accept connections within 21 seconds of the rollout start. — `database system is ready to accept connections` (O15, kubernetes-logs)
- The HorizontalPodAutoscaler for the edge service failed to retrieve metrics, suggesting the metrics-server or pods were under extreme stress. — `failed to get cpu utilization: unable to get metrics for resource cpu: no metrics returned from reso…` (O14, kubernetes)
- Prometheus metrics show zero restarts for the current recommendations pods since the rollout began. — `"container_restarts": [{"labels": {"pod": "recommendations-7bd4dd95d6-gfbqx"}, "points": 74, "from":…` (O19, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H2 | 0.90 | cause | resource_exhaustion | active | +4/−0 | kubernetes, prometheus | The simultaneous rollout of all workloads caused transient node-level resource exhaustion or containerd saturation. |
| H6 | 0.05 | cause | resource_exhaustion | active | +3/−0 | kubernetes, kubernetes-logs, prometheus | Postgres connection pool exhaustion due to low max_connections limit. |
| H7 | 0.02 | cause | configuration | active | +1/−1 | kubernetes | Workloads are failing to export telemetry due to the service rename. |
| H3 | 0.01 | cause | code_defect | active | +0/−0 |  | A code defect in version 1.4.0 causes intermittent crashes or health check failures. |
| H5 | 0.01 | symptom | resource_exhaustion | active | +0/−0 |  | Recommendations pods are crashing due to OOM or startup timeouts. |
| H1 | 0.00 | cause | configuration | retired (The errors in checkout logs (O5) and postgres probe failures…) | +0/−0 |  | The telemetry service rename caused a dependency failure for services attempting to export metrics/traces. |
| H4 | 0.00 | cause | dependency | retired (Postgres logs (O15) confirm the database is ready and accept…) | +1/−1 | kubernetes-logs | Postgres availability failure due to ImageInspectError. |

## Alternative explanations

- **H6**: While the Postgres max_connections limit of 40 is low, the presence of containerd socket errors and ImageInspectErrors suggests a broader infrastructure failure triggered by the rollout rather than a simple connection pool exhaustion.
- **H7**: The telemetry service rename occurred at 08:01Z, which is 8 minutes after the initial onset of probe failures and connection errors at 07:53Z.

<details><summary>Evidence for/against other hypotheses</summary>

- H4 supports (strong, O5/kubernetes-logs): `connection to server at "10.96.36.109", port 5432 failed: Connection refused` — Direct evidence that checkout cannot reach the database, which is a downstream effect of the postgres-0 failure.
- H4 contradicts (strong, O11/kubernetes): `"ready": true` — Postgres-0 is currently ready and running, meaning the ImageInspectError was transient and is not the cause of ongoing 5…
- H6 supports (moderate, O11/kubernetes): `"args": ["-c", "max_connections=40"` — A limit of 40 connections is very low for a microservices architecture during a full rollout, matching the 'Connection r…
- H7 supports (strong, O12/kubernetes): `{"name": "TELEMETRY_URL", "value": "http://telemetry-collector:8080/ingest"}` — The deployment is explicitly configured to use a service name that was deleted in O3.
- H7 contradicts (moderate, O14/kubernetes): `Readiness probe failed: Get "http://10.244.1.34:8080/healthz": dial tcp 10.244.1.34:8080: connect: c…` — Probe failures for recommendations and other services started at 07:53Z, which is 8 minutes before the telemetry service…
- H6 supports (weak, O5/kubernetes-logs): `error connecting in 'pool-<n>': connection failed: connection to server at "<ip>", port <n> failed: …` — Checkout is failing to connect to a dependency (likely Postgres), though 'Connection refused' is less specific than 'too…
- H6 supports (weak, O19/prometheus): `"request_rate_rps": [{"labels": {}, "points": 68, "from": "2026-10-14T07:55:09Z", "to": "2026-10-14T…` — The rapid increase in request rate across services following the rollout increases the likelihood of hitting the Postgre…

</details>

## Uncertainty

- Whether the 'Connection refused' errors in checkout were solely due to Postgres being down or if the low max_connections limit also contributed once the database became ready.
- The exact reason for the discrepancy between the reported 'restarting' pods and the zero restart count in Prometheus metrics, which may be due to pods failing to start entirely (ImageInspectError) rather than crashing after start.
- 5 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Implement staggered rollouts or use a deployment tool to limit the number of concurrent pod updates.
- Increase the Postgres max_connections limit to accommodate the connection requirements of all microservices.
- Review and potentially increase resource requests for the container runtime and kubelet to handle bursty workloads.
- Update the TELEMETRY_URL in service configurations to point to the new 'telemetry-collector-v2' service to prevent future telemetry export failures.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +1 accepted / 2 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `active_alerts` {} — what is alerting and since when → O1
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: continue; evidence +1 accepted / 2 rejected; new hypotheses ['H4', 'H5']
  - `pod_logs` {"namespace": "shop", "pod": "checkout-69cf4467b9-2cjfb"} — Check for errors related to telemetry-collector or upstream dependencies during the 502 window. → O5
  - `workload_metrics` {"namespace": "shop", "workload": "checkout"} — Determine the exact onset time of 5xx errors to see if they correlate with the rollout (07:53) or the telemetry change (08:01). → O6
  - `search_logs` {"namespace": "shop", "app": "recommendations", "level": "error"} — Find reasons for the reported restarts in recommendations pods, even if current pods are stable. → O7
  - `find_traces` {"service": "checkout", "errors_only": true} — Identify where the 502 errors are originating and what the specific error messages are. → O8
  - posteriors: H1=0.04, H2=0.39, H3=0.04, H4=0.39, H5=0.04, unexplained=0.11

**Round 2** — decision: continue; evidence +4 accepted / 0 rejected; new hypotheses ['H6', 'H7']; retired ['H1']
  - `query_metrics` {"promql": "sum(container_memory_working_set_bytes{namespace='shop'}) by (pod)"} — Check for memory spikes or OOM conditions across the namespace. → O9
  - `pod_logs` {"namespace": "shop", "pod": "inventory-77997799-abcde"} — Check if inventory is also failing due to database connection issues. → O10
  - `describe` {"kind": "pod", "namespace": "shop", "name": "postgres-0"} — Confirm the current state and error details of the database pod. → O11
  - `describe` {"kind": "deployment", "namespace": "shop", "name": "recommendations"} — Determine why recommendations pods are restarting (OOM, probe failure, or crash). → O12
  - posteriors: H2=0.52, H3=0.03, H4=0.03, H5=0.03, H6=0.08, H7=0.25, unexplained=0.07

**Round 3** — decision: continue; evidence +3 accepted / 1 rejected; new hypotheses []
  - `search_logs` {"namespace": "shop", "contains": "telemetry-collector"} — To confirm if services are failing due to the missing telemetry service. → O13
  - `get_events` {"namespace": "shop"} — To see the sequence of probe failures and restarts across all components. → O14
  - `pod_logs` {"namespace": "shop", "pod": "postgres-0"} — To check for connection limit errors in the database logs. → O15
  - posteriors: H2=0.77, H3=0.02, H4=0.02, H5=0.02, H6=0.09, H7=0.05, unexplained=0.04

**Round 4** — decision: confident: H2 p=0.90, margin 0.85, sources ['kubernetes', 'prometheus']; evidence +2 accepted / 0 rejected; new hypotheses []; retired ['H4']
  - `query_metrics` {"promql": "sum(container_cpu_usage_seconds_total{namespace='shop'}) by (pod)"} — Verify if there was a massive CPU spike across all pods during the 07:53Z rollout. → O16
  - `pod_logs` {"namespace": "shop", "pod": "recommendations-7bd4dd95d6-gfbqx", "previous": true} — Determine why recommendations pods are restarting (OOM, crash, or probe failure). → O17
  - `search_logs` {"namespace": "shop", "contains": "dial tcp: lookup telemetry-collector"} — Check if services are failing due to the telemetry service rename (H7). → O18
  - `workload_metrics` {"namespace": "shop", "workload": "recommendations"} — Check for OOM kills or restart patterns in recommendations. → O19
  - posteriors: H2=0.90, H3=0.01, H5=0.01, H6=0.05, H7=0.02, unexplained=0.02

Stop reason: confident: H2 p=0.90, margin 0.85, sources ['kubernetes', 'prometheus']

</details>