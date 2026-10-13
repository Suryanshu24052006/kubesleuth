# Checkout Service 502 Bad Gateway Incident

**Incident:** Checkout is intermittently failing with 502s; recommendations pods are restarting.  
**Namespace:** `shop` · **Investigation:** `20261013-123326-2e623e` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 6 rounds, 22 tool calls, 547.5s

## Root cause

A mass rollout of multiple shop workloads triggered container runtime resource contention and socket errors, leading to readiness probe failures in downstream dependencies (inventory and recommendations) which propagated upstream as 502s at the checkout and edge layers.

*Hypothesis H1 · component `node/kubesleuth-worker` · category `resource_exhaustion`*

**Confidence: INCONCLUSIVE** (posterior 0.14). Inconclusive: no hypothesis is supported well enough to be called the root cause.

## Causal chain

1. Simultaneous rollout of multiple deployments in the shop namespace initiated at 12:21 and 12:26. (O2)
2. Readiness probes for inventory and recommendations pods failed repeatedly due to connection refused and runtime communication issues. (O3, O20, O21)
3. Checkout experienced upstream connection errors and timeouts when attempting to reach downstream dependencies. (O18)
4. Checkout and edge latency increased, resulting in 502 Bad Gateway errors observed by clients. (O7, O12)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O3 | kubernetes | strong (+2.3) | `read unix @->/run/containerd/containerd.sock: read: connection reset by peer` | Direct evidence of the container runtime failing to respond to the kubelet. |
| ✅ O20 | kubernetes | strong (+1.38) | `Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from server: read unix @->/ru…` | Directly demonstrates containerd instability/connection resets during the mass rollout of workloads at 12:26. |
| ✅ O21 | kubernetes | strong (+0.828) | `Failed to create pod sandbox: rpc error: code = Unavailable desc = error reading from server: read unix @->/ru…` | Shows that containerd socket errors affected recommendations pods as well during the rollout. |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T12:17:30.161Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T12:21:12+00:00 | change | configmap/checkout-config last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:12+00:00 | change | configmap/edge-waf-rules last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:12+00:00 | change | configmap/feature-flags last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:12+00:00 | change | configmap/kube-root-ca.crt last-write (by kube-controller-manager) | O2 |
| 2026-10-13T12:21:12+00:00 | change | service/catalog-indexer last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:12+00:00 | change | service/checkout last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | rollout/catalog-indexer new-revision | O2 |
| 2026-10-13T12:21:13+00:00 | change | rollout/checkout new-revision | O2 |
| 2026-10-13T12:21:13+00:00 | change | rollout/edge new-revision | O2 |
| 2026-10-13T12:21:13+00:00 | change | rollout/inventory new-revision | O2 |
| 2026-10-13T12:21:13+00:00 | change | rollout/loadgen new-revision | O2 |
| 2026-10-13T12:21:13+00:00 | change | rollout/pricing new-revision | O2 |
| 2026-10-13T12:21:13+00:00 | change | rollout/recommendations new-revision | O2 |
| 2026-10-13T12:21:13+00:00 | change | rollout/review-bot new-revision | O2 |
| 2026-10-13T12:21:13+00:00 | change | rollout/telemetry-collector new-revision | O2 |
| 2026-10-13T12:21:13+00:00 | change | service/edge last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | service/inventory last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | service/postgres last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | service/pricing last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | service/recommendations last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | deployment/catalog-indexer last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | deployment/loadgen last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | deployment/pricing last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | deployment/review-bot last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | deployment/telemetry-collector last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | statefulset/postgres last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13+00:00 | change | hpa/edge last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T12:21:13Z | event | event ScalingReplicaSet x1 on Deployment/inventory: Scaled up replica set inventory-6ffc77fd45 from 0 to 4 | O20 |
| 2026-10-13T12:21:13Z | event | event ScalingReplicaSet x1 on Deployment/recommendations: Scaled up replica set recommendations-7bd4dd95d6 from 0 to 2 | O21 |

## Observed facts

- Widespread readiness probe failures (connection refused) began immediately after the rollout across multiple services. — `Readiness probe failed: Get "http://10.244.1.22:8080/readyz": dial tcp 10.244.1.22:8080: connect: co…` (O3, kubernetes)
- The container runtime (containerd) experienced connection resets, failing pod creation and deletion at 12:26:23. — `rpc error: code = Unavailable desc = error reading from server: read unix @->/run/containerd/contain…` (O3, kubernetes)
- Even the postgres-0 statefulset experienced readiness probe failures due to containerd connection issues. — `Readiness probe errored and resulted in unknown state: rpc error: code = Unavailable desc = connecti…` (O3, kubernetes)
- No traces were found for the checkout service, indicating a total failure of telemetry collection. — `traces_examined: 0, traces_with_errors: 0` (O8, jaeger)
- Inventory and recommendations pods are failing readiness probes with connection timeouts. — `Readiness probe failed: Get "http://10.244.1.53:8080/healthz": dial tcp 10.244.1` (O3, kubernetes)
- Checkout is configured to send OTLP spans to jaeger in observability namespace, not telemetry-collector in shop. — `"OTEL_EXPORTER_OTLP_ENDPOINT", "value": "http://jaeger.observability.svc:4318"` (O9, kubernetes)
- Checkout deployment has 3 ready replicas running revision 2. — `"availableReplicas": 3, "observedGeneration": 2, "readyReplicas": 3, "replicas": 3` (O9, kubernetes)
- Edge is experiencing dependency timeouts when calling checkout. — `"dep": "checkout", "outcome": "timeout"` (O12, prometheus)
- Edge p95 latency spiked from 0.24s to 1.68s at 12:27:01Z. — `"onset": {"time": "2026-10-13T12:27:01Z", "direction": "increase", "baseline": 0.241124, "value_afte…` (O12, prometheus)
- Log search for telemetry errors across the namespace returned zero records. — `{namespace="shop", level="error"} |= "telemetry"` (O10, loki)
- Recommendations deployment references jaeger.observability.svc for OTLP export. — `"OTEL_EXPORTER_OTLP_ENDPOINT", "value": "http://jaeger.observability.svc:4318"` (O14, kubernetes)
- Recommendations deployment references TELEMETRY_URL using the old telemetry-collector service name. — `"TELEMETRY_URL", "value": "http://telemetry-collector:8080/ingest"` (O14, kubernetes)
- Recommendations application restarted and successfully completed server startup. — `INFO: Started server process [1]` (O15, loki)
- Checkout logs show upstream connection errors to inventory/recommendations. — `upstream connection error error=ConnectError detail=All connection attempts failed` (O18, kubernetes-logs)
- Checkout logs show upstream timeout errors. — `upstream timeout error=timeout` (O18, kubernetes-logs)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.14 | cause | resource_exhaustion | active | +3/−0 | kubernetes | Container runtime (containerd) instability or crash on the worker node. |
| H6 | 0.00 | cause | probe_misconfiguration | active | +0/−0 |  | Recommendations deployment has a probe misconfiguration or startup crash preventing it from serving traffic. |
| H7 | 0.00 | cause | dependency | active | +0/−0 |  | Inventory service readiness failure causes checkout to hang and time out, propagating 502s upstream to edge. |
| H8 | 0.00 | cause | configuration | active | +0/−0 |  | Applications are timing out or blocking on synchronous HTTP telemetry calls to the deleted telemetry-collector service. |
| H3 | 0.84 | symptom | dependency | active | +6/−0 | kubernetes, kubernetes-logs, prometheus | Checkout 502s are symptoms of downstream dependency failures (Inventory/Recommendations). |
| H5 | 0.01 | symptom | networking | active | +1/−0 | prometheus | Edge/Ingress is returning 502s because checkout pods are unready or timing out. |
| H2 | 0.00 | cause | dependency | retired (Checkout is configured to use jaeger.observability.svc direc…) | +1/−2 | jaeger | Telemetry collector failure causing upstream timeouts and 502s. |
| H4 | 0.00 | cause | configuration | retired (OTEL_EXPORTER_OTLP_ENDPOINT in checkout points to jaeger in …) | +0/−1 |  | Services are hanging on synchronous telemetry exports to a missing or unreachable collector. |

## Alternative explanations

- **H2**: Log search showed zero telemetry errors, and checkout explicitly points to an external jaeger endpoint rather than the deleted telemetry-collector.
- **H4**: Configuration inspection confirmed OTEL_EXPORTER_OTLP_ENDPOINT points to a valid external service outside the shop namespace scope that was modified.
- **H8**: No connection refused or timeout errors to the telemetry-collector service were present in application logs.

<details><summary>Evidence for/against other hypotheses</summary>

- H3 supports (moderate, O3/kubernetes): `Readiness probe failed: Get "http://10.244.1.54:8080/healthz": dial tcp 10.244.1.54:8080: connect: c…` — Widespread probe failures in dependencies directly cause 502s in the caller.
- H2 supports (strong, O8/jaeger): `traces_examined: 0, traces_with_errors: 0` — Zero traces found for a service with 20 RPS strongly indicates the telemetry pipeline is broken.
- H2 contradicts (strong, O9/kubernetes): `"OTEL_EXPORTER_OTLP_ENDPOINT", "value": "http://jaeger.observability.svc:4318"` — Checkout exports telemetry to jaeger in observability namespace, not telemetry-collector in shop.
- H4 contradicts (strong, O9/kubernetes): `"OTEL_EXPORTER_OTLP_ENDPOINT", "value": "http://jaeger.observability.svc:4318"` — Checkout configuration does not point to the telemetry-collector service that was deleted or renamed.
- H2 contradicts (moderate, O10/loki): `{namespace="shop", level="error"} |= "telemetry"` — No telemetry error logs found in Loki across shop pods.
- H5 supports (strong, O12/prometheus): `"dep": "checkout", "outcome": "timeout"` — Edge metrics confirm timeouts when calling checkout, leading to edge 5xx errors.
- H3 supports (moderate, O12/prometheus): `"onset": {"time": "2026-10-13T12:27:01Z", "direction": "increase", "baseline": 0.241124, "value_afte…` — Edge latency spike mirrors checkout latency increase, confirming upstream symptom propagation.
- H3 supports (weak, O14/kubernetes): `TELEMETRY_URL` — Shows configuration dependencies are present across workloads.
- H3 supports (strong, O18/kubernetes-logs): `upstream connection error error=ConnectError detail=All connection attempts failed` — Checkout connection failures to dependencies explain the 502s and latency spikes.
- H3 supports (strong, O20/kubernetes): `Readiness probe failed: Get "http://10.244.1.53:8080/healthz": dial tcp 10.244.1.53:8080: connect: c…` — Confirms readiness probe failures on inventory pods, validating the downstream dependency failure symptom leading to che…
- H3 supports (strong, O21/kubernetes): `Readiness probe failed: Get "http://10.244.1.54:8080/healthz": dial tcp 10.244.1.54:8080: connect: c…` — Confirms recommendations probe failures, contributing to the upstream service degradation.

</details>

## Uncertainty

- Exact metric-level resource utilization for containerd on the worker node during the initial rollout spike due to metric scraping limitations.
- Whether rolling updates can be staggered to prevent simultaneous container initialization stress.
- 4 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Implement staggered rolling update strategies for dependent services to avoid simultaneous resource and container runtime pressure.
- Review and tune liveness and readiness probe initial delay settings for inventory and recommendations services.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +2 accepted / 1 rejected; new hypotheses ['H1', 'H2', 'H3']
  - `active_alerts` {} — what is alerting and since when → O1
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O2
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: continue; evidence +1 accepted / 3 rejected; new hypotheses ['H4', 'H5']
  - `query_metrics` {"promql": "sum(rate(container_cpu_usage_seconds_total{namespace='shop'}[2m])) by (pod)"} — Check for CPU spikes during the 12:21 rollout that could have crashed containerd. → O5
  - `pod_logs` {"namespace": "shop", "pod": "recommendations-58866dbd86-8wlzh", "previous": true} — Check why recommendations pods were restarting (OOM, crash, or probe failure). → O6
  - `workload_metrics` {"namespace": "shop", "workload": "checkout"} — Confirm 5xx onset time and identify if it correlates with dependency failures. → O7
  - `find_traces` {"service": "checkout", "errors_only": true} — Identify the exact service and operation where checkout errors originate. → O8
  - posteriors: H1=0.36, H2=0.36, H3=0.12, H4=0.04, H5=0.04, unexplained=0.10

**Round 2** — decision: continue; evidence +5 accepted / 0 rejected; new hypotheses ['H6', 'H7']
  - `describe` {"kind": "deployment", "namespace": "shop", "name": "checkout"} — Check environment variables for telemetry endpoints (OTEL_EXPORTER_OTLP_ENDPOINT) to see if they match the new service name. → O9
  - `search_logs` {"namespace": "shop", "contains": "telemetry", "level": "error"} — Look for explicit connection errors to the telemetry collector across all pods. → O10
  - `get_events` {"namespace": "shop", "involved_name": "telemetry-collector-v2"} — Check if the new telemetry collector is actually running and healthy. → O11
  - `workload_metrics` {"namespace": "shop", "workload": "edge"} — Verify if 502s are originating at the edge layer and check its dependency failure metrics. → O12
  - posteriors: H1=0.28, H2=0.01, H3=0.30, H4=0.00, H5=0.28, H6=0.03, H7=0.03, unexplained=0.07

**Round 3** — decision: continue; evidence +1 accepted / 0 rejected; new hypotheses ['H8']; retired ['H2', 'H4']
  - `describe` {"kind": "deployment", "namespace": "shop", "name": "inventory"} — Check probe configuration, container ports, and status for inventory pods experiencing probe failures. → O13
  - `describe` {"kind": "deployment", "namespace": "shop", "name": "recommendations"} — Check probe configuration, container ports, environment, and readiness status for recommendations. → O14
  - `search_logs` {"namespace": "shop", "app": "recommendations", "minutes": 30} — Inspect application logs from recommendations to identify crash reasons or port binding errors. → O15
  - `workload_metrics` {"namespace": "shop", "workload": "recommendations"} — Check restart counts, latency, and request rates for recommendations. → O16
  - posteriors: H1=0.25, H3=0.37, H5=0.25, H6=0.03, H7=0.03, H8=0.03, unexplained=0.07

**Round 4** — decision: continue; evidence +1 accepted / 0 rejected; new hypotheses []
  - `search_logs` {"namespace": "shop", "contains": "telemetry"} — Check for errors related to telemetry export failures in the shop namespace logs. → O17
  - `pod_logs` {"namespace": "shop", "pod": "checkout-8457f655f7-9hmfj", "tail": 100} — Examine checkout logs to see why p95 latency increased and if connection errors are occurring. → O18
  - posteriors: H1=0.06, H3=0.85, H5=0.06, H6=0.01, H7=0.01, H8=0.01, unexplained=0.02

**Round 5** — decision: continue; evidence +4 accepted / 0 rejected; new hypotheses []
  - `pod_logs` {"namespace": "shop", "pod": "inventory-668745bb49-5xmp9"} — Inspect inventory logs to find the cause of probe failures. → O19
  - `get_events` {"namespace": "shop", "involved_name": "inventory"} — Check inventory events to see why readiness probes failed. → O20
  - `get_events` {"namespace": "shop", "involved_name": "recommendations"} — Check recommendations events to see why readiness probes failed or pods restarted. → O21
  - `workload_metrics` {"namespace": "shop", "workload": "inventory"} — Check inventory workload metrics for latency, restarts, and error rates. → O22
  - posteriors: H1=0.14, H3=0.84, H5=0.01, H6=0.00, H7=0.00, H8=0.00, unexplained=0.00

**Round 6** — decision: round budget exhausted; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.14, H3=0.84, H5=0.01, H6=0.00, H7=0.00, H8=0.00, unexplained=0.00

Stop reason: round budget exhausted

</details>