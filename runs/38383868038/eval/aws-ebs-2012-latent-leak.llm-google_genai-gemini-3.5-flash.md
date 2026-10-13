# Checkout 502s and Pod Restarts due to Telemetry Service Rename

**Incident:** Checkout is intermittently failing with 502s; recommendations pods are restarting.  
**Namespace:** `shop` · **Investigation:** `20261013-105120-c0820f` · **Reasoner:** `llm:google_genai:gemini-3.5-flash` · 2 rounds, 12 tool calls, 215.6s

## Root cause

The 'telemetry-collector' service was renamed to 'telemetry-collector-v2' without updating application configurations, causing DNS resolution failures and resource exhaustion due to telemetry event buffering.

**Confidence: INCONCLUSIVE** (posterior 0.00). Inconclusive: no hypothesis is supported well enough to be called the root cause.

## Causal chain

1. The 'telemetry-collector' service was deleted and replaced by 'telemetry-collector-v2' at 10:47:45Z. (O2)
2. Application pods (recommendations, inventory) failed to resolve the old 'telemetry-collector' hostname, leading to 'Temporary failure in name resolution' errors. (O5)
3. Telemetry clients began buffering events locally, causing a sharp increase in memory usage and CPU throttling. (O8, O10)
4. Resource exhaustion and/or blocking telemetry calls caused readiness and liveness probes to fail for recommendations, inventory, and edge services. (O3)
5. The checkout service experienced timeouts and connection failures when attempting to call the unhealthy inventory service. (O11, O12)
6. The edge service returned 502 errors to users due to the unavailability of upstream services and its own health check failures. (O3)

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:38:50+00:00 | change | configmap/checkout-config last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:50+00:00 | change | configmap/edge-waf-rules last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:50+00:00 | change | configmap/feature-flags last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:50+00:00 | change | configmap/kube-root-ca.crt last-write (by kube-controller-manager) | O2 |
| 2026-10-13T10:38:50+00:00 | change | service/catalog-indexer last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:51+00:00 | change | service/checkout last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:51+00:00 | change | service/edge last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:51+00:00 | change | service/inventory last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:51+00:00 | change | service/postgres last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:52+00:00 | change | rollout/catalog-indexer new-revision | O2 |
| 2026-10-13T10:38:52+00:00 | change | rollout/checkout new-revision | O2 |
| 2026-10-13T10:38:52+00:00 | change | rollout/edge new-revision | O2 |
| 2026-10-13T10:38:52+00:00 | change | rollout/inventory new-revision | O2 |
| 2026-10-13T10:38:52+00:00 | change | rollout/loadgen new-revision | O2 |
| 2026-10-13T10:38:52+00:00 | change | rollout/pricing new-revision | O2 |
| 2026-10-13T10:38:52+00:00 | change | rollout/recommendations new-revision | O2 |
| 2026-10-13T10:38:52+00:00 | change | rollout/review-bot new-revision | O2 |
| 2026-10-13T10:38:52+00:00 | change | service/pricing last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:52+00:00 | change | service/recommendations last-write (by kubectl-client-side-apply) | O2 |
| 2026-10-13T10:38:53+00:00 | change | rollout/telemetry-collector new-revision | O2 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x9 on Pod/edge-555d7c4d58-d59d9,edge-555d7c4d58-g7bqs: Readiness probe failed: Get "http://10.244.1.50:8080/healthz": dial tcp 10.244.… | O3 |
| 2026-10-13T10:38:56Z | event | event Unhealthy x22 on Pod/inventory-6f6c46876d-2ccsv,inventory-6f6c46876d-6xqxs: Readiness probe failed: Get "http://10.244.1.48:8080/healthz": dial … | O3 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x12 on Pod/recommendations-67c55868cc-2mk82,recommendations-67c55868cc-5f6w2: Readiness probe failed: Get "http://10.244.1.52:8080/hea… | O3 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x22 on Pod/checkout-69cf4467b9-9p4zs,checkout-69cf4467b9-f5wmb: Readiness probe failed: Get "http://10.244.1.25:8080/readyz": dial tcp… | O3 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x11 on Pod/catalog-indexer-6f6b545fdb-4kfvf,catalog-indexer-6f6b545fdb-mtscn: Readiness probe failed: Get "http://10.244.1.19:8080/hea… | O3 |
| 2026-10-13T10:38:57Z | event | event Unhealthy x5 on Pod/pricing-95c99775f-5sx5n,pricing-95c99775f-8drxw: Readiness probe failed: Get "http://10.244.1.26:8080/healthz": dial tcp 10.… | O3 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x3 on Pod/telemetry-collector-865ccb84c6-ckttb: Readiness probe failed: Get "http://10.244.1.36:8080/healthz": dial tcp 10.244.1.36:80… | O3 |
| 2026-10-13T10:38:58Z | event | event Unhealthy x2 on Pod/edge-6675f7688f-5jhhr,edge-6675f7688f-xnt2d: Liveness probe failed: Get "http://10.244.1.20:8080/healthz": dial tcp 10.244.1… | O3 |
| 2026-10-13T10:39:00Z | log | first log: error connecting in 'pool-<n>': connection failed: connection to server at "<ip>", port <n… (x47) | O12 |

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|

## Alternative explanations

- **Resource limit insufficiency**: While CPU throttling was observed, the onset perfectly correlates with the telemetry service name change and DNS errors, suggesting the resource pressure is a secondary effect of the telemetry failure.
- **Database (Postgres) saturation**: Logs specifically highlight telemetry DNS failures and upstream timeouts between microservices, rather than database connection pool exhaustion or slow queries.

## Uncertainty

- It is unclear why the telemetry client in these services is configured to buffer in a way that impacts process health (e.g., blocking calls or unbounded memory growth).
- The exact configuration mechanism (ConfigMap vs Env Var) used to point services to the telemetry collector was not explicitly inspected.

## Suggested remediation (not executed — the agent is read-only)

- Create a Service alias or rename 'telemetry-collector-v2' back to 'telemetry-collector' to immediately restore connectivity.
- Update the 'feature-flags' or 'checkout-config' ConfigMaps to point to the new 'telemetry-collector-v2' endpoint if the rename is intended.
- Configure telemetry clients to use non-blocking exports and implement strict memory limits for buffers to prevent sidecar/dependency failures from crashing the main application.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +0 accepted / 0 rejected; new hypotheses []
  - `active_alerts` {} — what is alerting and since when → O1
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O2
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []; notes: hypothesize failed: model failed to produce HypothesisUpdate: Error calling model 'gemini-3.5-flash' (RESOURCE_EXHAUSTED): 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 5, model: gemini-3.6-flash\nPlease retry in 1.563116539s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'model': 'gemini-3.6-flash', 'location': 'global'}, 'quotaValue': '5'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '1s'}]}}. assess failed: model failed to produce Step: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}. 
  - `search_logs` {"namespace": "shop", "app": "recommendations", "minutes": 30} — Search recent logs across recommendations pods to identify errors or panic/crash messages prior to container restarts. → O5
  - `pod_logs` {"namespace": "shop", "pod": "recommendations-67c55868cc-2mk82", "previous": true} — Inspect previous container logs for recommendations pod recommendations-67c55868cc-2mk82 to see why liveness/readiness failed or container crashed. → O6
  - `find_traces` {"service": "checkout", "minutes": 30, "errors_only": true} — Trace 502 errors originating from checkout requests down through its upstream/downstream dependencies to see where the call fails. → O7
  - `workload_metrics` {"namespace": "shop", "workload": "recommendations", "minutes": 30} — Check golden signals, CPU/Memory metrics, throttling, and onset time for recommendations. → O8
  - posteriors: unexplained=1.00

**Round 2** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []; notes: hypothesize failed: model failed to produce HypothesisUpdate: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}. assess failed: model failed to produce Step: Failed to parse Step from completion {"facts": [{"observation_id": "O9", "quote": "\"TELEMETRY_URL\", \"value\": \"http://telemetry-collector:8080/ingest\"", "statement": "Deployment recommendations is configured to send telemetry to http://telemetry-collector:8080/ingest.", "time": "2026-10-13T10:38:52Z"}, {"observation_id": "O10", "quote": "\"pod\": \"recommendations-67c55868cc-2mk82\", \"service\": \"recommendations\", \"svc\": \"recommendations\"}, \"points\": 18, \"from\": \"2026-10-13T10:44:47Z\", \"to\": \"2026-10-13T10:53:17Z\", \"first\": 6.0, \"last\": 64.0", "statement": "Telemetry buffered events for recommendations pod 2mk82 increased steadily up to 64 after 10:48:47Z.", "time": "2026-10-13T10:48:47Z"}, {"observation_id": "O11", "quote": "\"latency_p95_seconds\": [{\"labels\": {}, \"points\": 54, \"from\": \"2026-10-13T10:40:02Z\", \"to\": \"2026-10-13T10:53:17Z\", \"first\": 0.4776, \"last\": 1.668", "statement": "Checkout p95 latency surged from 0.48s to 1.67s starting around 10:45:02Z.", "time": "2026-10-13T10:45:02Z"}, {"observation_id": "O12", "quote": "\"pattern\": \"upstream returned error upstream=inventory status=<n> body={\\\"error\\\":\\\"stock lookup failed\\\"}\"", "statement": "Checkout service encountered 33 HTTP 500 errors from inventory during stock lookups.", "time": "2026-10-13T10:39:15Z"}, {"observation_id": "O12", "quote": "\"pattern\": \"upstream timeout error=timeout\"", "statement": "Checkout service encountered 52 upstream timeout errors.", "time": "2026-10-13T10:39:17Z"}], "new_hypotheses": [{"statement": "The deletion of service/telemetry-collector and replacement with service/telemetry-collector-v2 broke DNS resolution for recommendations, causing event buffer build-up and probe failures.", "mechanism": "recommendations service attempts to flush telemetry to http://telemetry-collector:8080/ingest. When service/telemetry-collector was deleted at 10:47:45, DNS lookups failed, leading to buffered events accumulation and synchronous blocking or resource pressure that triggered readiness and liveness probe failures.", "component": "service/telemetry-collector", "category": "configuration", "layer": "cause", "predictions": ["search_logs for app=recommendations will show DNS resolution errors for telemetry-collector", "describe deployment/recommendations shows TELEMETRY_URL referencing telemetry-collector rather than telemetry-collector-v2"]}, {"statement": "Checkout service requests are failing or timing out due to upstream failures and latency in the inventory service.", "mechanism": "Checkout calls inventory for stock lookups. Inventory service generates HTTP 500 errors ('stock lookup failed') or timeouts, causing checkout p95 latency to increase and edge proxy to fail requests with 502s.", "component": "inventory", "category": "dependency", "layer": "cause", "predictions": ["search_logs for app=inventory will show database connection errors or internal stock lookup exceptions", "workload_metrics for inventory will show error rates or high latency matching checkout onset"]}, {"statement": "Edge proxy is returning 502s due to transient backend connection timeouts and readiness probe failures.", "mechanism": "Edge proxy fails readiness probes when upstream checkout/recommendations are slow or failing health checks, returning 502 Bad Gateway to clients.", "component": "edge", "category": "networking", "layer": "symptom", "predictions": ["search_logs for app=edge will reveal upstream connection refused or timeout errors when talking to checkout"]}], "retire": [], "evidence": [{"hypothesis_id": "N1", "observation_id": "O9", "quote": "\"TELEMETRY_URL\", \"value\": \"http://telemetry-collector:8080/ingest\"", "stance": "supports", "strength": "strong", "rationale": "Directly demonstrates recommendations deployment is configured with the old telemetry service name http://telemetry-collector:8080/ingest."}, {"hypothesis_id": "N1", "observation_id": "O10", "quote": "\"pod\": \"recommendations-67c55868cc-2mk82\", \"service\": \"recommendations\", \"svc\": \"recommendations\"}, \"points\": 18, \"from\": \"2026-10-13T10:44:47Z\", \"to\": \"2026-10-13T10:53:17Z\", \"first\": 6.0, \"last\": 64.0", "stance": "supports", "strength": "strong", "rationale": "Shows buffered events accumulating in recommendations right after telemetry-collector service was deleted at 10:47:45Z."}, {"hypothesis_id": "N2", "observation_id": "O11", "quote": "\"latency_p95_seconds\": [{\"labels\": {}, \"points\": 5"}]}. Got: 1 validation error for Step
evidence.2.stance
  Field required [type=missing, input_value={'hypothesis_id': 'N2', '...bels": {}, "points": 5'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/missing
For troubleshooting, visit: https://docs.langchain.com/oss/python/langchain/errors/OUTPUT_PARSING_FAILURE . 
  - `describe` {"kind": "deployment", "namespace": "shop", "name": "recommendations"} — Inspect recommendations deployment environment variables and telemetry configuration. → O9
  - `query_metrics` {"promql": "telemetry_buffered_events{namespace=\"shop\"}", "minutes": 30} — Measure telemetry buffered event growth across services following the deletion of telemetry-collector service. → O10
  - `workload_metrics` {"namespace": "shop", "workload": "checkout"} — Check golden signals, 5xx ratios, and dependency failure metrics for the checkout service. → O11
  - `search_logs` {"namespace": "shop", "app": "checkout", "minutes": 30} — Find error logs in checkout to see which downstream dependencies (e.g. recommendations or telemetry) are timing out or failing. → O12
  - posteriors: unexplained=1.00

Stop reason: no new evidence for two rounds

</details>