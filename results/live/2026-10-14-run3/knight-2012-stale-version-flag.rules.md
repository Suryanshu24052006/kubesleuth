# RCA: Newly created workload pricing-legacy serves traffic with different code

**Incident:** Checkout errors jumped to roughly a third of requests a few minutes ago.  
**Namespace:** `shop` · **Investigation:** `20261014-085731-b65ec1` · **Reasoner:** `rules` · 4 rounds, 9 tool calls, 0.3s

## Root cause

Newly created workload pricing-legacy serves traffic with different code

*Hypothesis H2 · component `pricing-legacy` · category `version_skew`*

**Confidence: LOW** (posterior 0.43). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. 'legacy' observed near pricing-legacy: amespace": "shop", "workload": "pricing-legacy", "window_minutes": 30, "step_sec (O5)
2. 'legacy' observed near pricing-legacy: y", "kind": "Pod", "objects": ["pricing-legacy-79659db7cf-n2xt5"], "message": "R (O2)
3. 'legacy' observed near pricing-legacy: , "namespace": "shop", "name": "pricing-legacy", "change": "created", "fields":  (O3)
4. 'legacy' observed near pricing-legacy: 2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 's (O4)
5. 'legacy' observed near pricing-legacy: _pod_rps": [{"labels": {"pod": "pricing-legacy-79659db7cf-n2xt5"}, "points": 5,  (O9)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O5 | prometheus | moderate (+1.2) | `amespace": "shop", "workload": "pricing-legacy", "window_minutes": 30, "step_seconds": 15, "signals": {"cp` | 'legacy' observed near pricing-legacy |
| ✅ O2 | kubernetes | moderate (+1.2) | `y", "kind": "Pod", "objects": ["pricing-legacy-79659db7cf-n2xt5"], "message": "Readiness probe failed: Get` | 'legacy' observed near pricing-legacy |
| ✅ O3 | kubernetes | moderate (+0.72) | `, "namespace": "shop", "name": "pricing-legacy", "change": "created", "fields": [], "actor": {"manager": "` | 'legacy' observed near pricing-legacy |
| ✅ O4 | kubernetes | moderate (+0.432) | `2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 'shop:1.4.0']"], "workloads"` | 'legacy' observed near pricing-legacy |
| ✅ O9 | prometheus | moderate (+0.72) | `_pod_rps": [{"labels": {"pod": "pricing-legacy-79659db7cf-n2xt5"}, "points": 5, "from": "2026-10-14T08:56:` | 'legacy' observed near pricing-legacy |

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
| 2026-10-14T08:31:02Z | onset | edge cpu_throttled_ratio on 2/3 series increase: 0.0 → 0.4507 | O6 |
| 2026-10-14T08:31:12Z | event | event Unhealthy x35 on Pod/edge-6675f7688f-dtglc,edge-6675f7688f-qfm4b: Liveness probe failed: Get "http://10.244.1.22:8080/healthz": context deadline… | O2 |
| 2026-10-14T08:31:13Z | event | event Unhealthy x51 on Pod/edge-6675f7688f-dtglc,edge-6675f7688f-qfm4b: Readiness probe failed: Get "http://10.244.1.22:8080/healthz": context deadlin… | O2 |
| 2026-10-14T08:31:47Z | onset | edge errors_by_pod_rps on 2/3 series increase: 0.0 → 0.981201 | O6 |
| 2026-10-14T08:31:47Z | onset | edge container_restarts on 2/3 series increase: 0.0 → 2.0 | O6 |
| 2026-10-14T08:31:47Z | onset | edge errors_by_pod_rps on 2/3 series increase: 0.0 → 0.981256 | O8 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-14T08:40:02Z — `2026-10-14T08:40:02Z` (O6, prometheus)
- edge error_ratio_5xx increase at 2026-10-14T08:40:02Z — `2026-10-14T08:40:02Z` (O8, prometheus)
- edge error_ratio_5xx increase at 2026-10-14T08:40:02Z — `2026-10-14T08:40:02Z` (O6, prometheus)
- edge error_ratio_5xx increase at 2026-10-14T08:40:02Z — `2026-10-14T08:40:02Z` (O8, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H2 | 0.43 | cause | version_skew | active | +5/−0 | kubernetes, prometheus | Newly created workload pricing-legacy serves traffic with different code |
| H6 | 0.43 | cause | version_skew | active | +5/−0 | kubernetes, prometheus | Service pricing mixes versions of its backend |
| H5 | 0.08 | cause | capacity | active | +6/−0 | kubernetes, prometheus | Capacity of edge was reduced (spec.replicas 3->2) |
| H3 | 0.02 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap checkout-config change (data.DB_POOL_SIZE 30->4) broke a dependent service |
| H1 | 0.01 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap feature-flags change (data.flags.json {"smart_routing": false, "new_checkout_ui": true} ->{"smart_routing": tr… |
| H4 | 0.01 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap edge-waf-rules change (data.rules.json {"rules": [ {"id": "sqli-union-select", "pattern": "(?i)union\\s+select… |

<details><summary>Evidence for/against other hypotheses</summary>

- H5 supports (weak, O6/prometheus): `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 121, "from": "2026-10-14T08:27:32Z", "t…` — 'timeout' observed
- H5 supports (weak, O5/prometheus): `2\u2581\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "pricing-legacy-79659d…` — 'throttl' observed
- H5 supports (weak, O8/prometheus): `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 121, "from": "2026-10-14T08:27:32Z", "t…` — 'timeout' observed
- H1 supports (weak, O2/kubernetes): `\": dial tcp 10.244.1.63:8080: connect: connection refused", "count": 2, "first_seen": "2026-10-14T0…` — 'connection' observed
- H3 supports (weak, O2/kubernetes): `\": dial tcp 10.244.1.63:8080: connect: connection refused", "count": 2, "first_seen": "2026-10-14T0…` — 'connection' observed
- H4 supports (weak, O2/kubernetes): `\": dial tcp 10.244.1.63:8080: connect: connection refused", "count": 2, "first_seen": "2026-10-14T0…` — 'connection' observed
- H5 supports (moderate, O2/kubernetes): `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 35, "fir…` — 'timeout' observed near edge
- H1 supports (weak, O3/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "30", "new": "4", "in_effect": true}], "a…` — 'pool' observed
- H3 supports (moderate, O3/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "30", "new": "4", "in_effect": true}], "a…` — 'pool' observed near checkout-config
- H4 supports (weak, O3/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "30", "new": "4", "in_effect": true}], "a…` — 'pool' observed
- H5 supports (weak, O3/kubernetes): `econds\": 5, \"successThreshold\": 1, \"timeoutSeconds\": 1}", "new": "{\"failureThreshold\": 3, \"h…` — 'timeout' observed
- H5 supports (weak, O9/prometheus): `2\u2582\u2581", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "pricing-95c99775f-rtm…` — 'throttl' observed
- H6 supports (moderate, O9/prometheus): `_pod_rps": [{"labels": {"pod": "pricing-legacy-79659db7cf-n2xt5"}, "points": 5, "from": "2026-10-14T…` — 'legacy' observed near pricing
- H6 supports (moderate, O2/kubernetes): `y", "kind": "Pod", "objects": ["pricing-legacy-79659db7cf-n2xt5"], "message": "Readiness probe faile…` — 'legacy' observed near pricing
- H6 supports (moderate, O3/kubernetes): `, "namespace": "shop", "name": "pricing-legacy", "change": "created", "fields": [], "actor": {"manag…` — 'legacy' observed near pricing
- H6 supports (moderate, O4/kubernetes): `2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 'shop:1.4.0']"], "work…` — 'legacy' observed near pricing
- H6 supports (moderate, O5/prometheus): `amespace": "shop", "workload": "pricing-legacy", "window_minutes": 30, "step_seconds": 15, "signals"…` — 'legacy' observed near pricing

</details>

## Uncertainty

- Baseline rule reasoner: causal links are keyword-based, verify manually.
- 15 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Review and revert the implicated change if confirmed.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +0 accepted / 0 rejected; new hypotheses []
  - `active_alerts` {} — what is alerting and since when → O1
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O4

**Round 1** — decision: continue; evidence +15 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3', 'H4', 'H5']
  - `workload_metrics` {"namespace": "shop", "workload": "pricing-legacy", "minutes": 30} — test H2 → O5
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O6
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O7
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — test H5 → O8
  - posteriors: H1=0.04, H2=0.61, H3=0.06, H4=0.04, H5=0.21, unexplained=0.05

**Round 2** — decision: continue; evidence +7 accepted / 15 rejected; new hypotheses ['H6']
  - `workload_metrics` {"namespace": "shop", "workload": "pricing", "minutes": 30} — test H6 → O9
  - posteriors: H1=0.01, H2=0.43, H3=0.02, H4=0.01, H5=0.08, H6=0.43, unexplained=0.02

**Round 3** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.01, H2=0.43, H3=0.02, H4=0.01, H5=0.08, H6=0.43, unexplained=0.02

**Round 4** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.01, H2=0.43, H3=0.02, H4=0.01, H5=0.08, H6=0.43, unexplained=0.02

Stop reason: no new evidence for two rounds

</details>