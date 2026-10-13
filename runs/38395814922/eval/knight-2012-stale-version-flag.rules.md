# RCA: Newly created workload pricing-legacy serves traffic with different code

**Incident:** Checkout errors jumped to roughly a third of requests a few minutes ago.  
**Namespace:** `shop` · **Investigation:** `20261013-133030-c1179d` · **Reasoner:** `rules` · 4 rounds, 9 tool calls, 0.8s

## Root cause

Newly created workload pricing-legacy serves traffic with different code

*Hypothesis H2 · component `pricing-legacy` · category `version_skew`*

**Confidence: LOW** (posterior 0.39). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. 'legacy' observed near pricing-legacy: amespace": "shop", "workload": "pricing-legacy", "window_minutes": 30, "step_sec (O6)
2. 'legacy' observed near pricing-legacy: , "namespace": "shop", "name": "pricing-legacy", "change": "created", "fields":  (O2)
3. 'legacy' observed near pricing-legacy: 2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 's (O3)
4. 'legacy' observed near pricing-legacy: y", "kind": "Pod", "objects": ["pricing-legacy-79659db7cf-2lnp8"], "message": "R (O4)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O6 | prometheus | moderate (+1.2) | `amespace": "shop", "workload": "pricing-legacy", "window_minutes": 30, "step_seconds": 15, "signals": {"cp` | 'legacy' observed near pricing-legacy |
| ✅ O2 | kubernetes | moderate (+1.2) | `, "namespace": "shop", "name": "pricing-legacy", "change": "created", "fields": [], "actor": {"manager": "` | 'legacy' observed near pricing-legacy |
| ✅ O3 | kubernetes | moderate (+0.72) | `2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 'shop:1.4.0']"], "workloads"` | 'legacy' observed near pricing-legacy |
| ✅ O4 | kubernetes | moderate (+0.432) | `y", "kind": "Pod", "objects": ["pricing-legacy-79659db7cf-2lnp8"], "message": "Readiness probe failed: Get` | 'legacy' observed near pricing-legacy |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T12:17:30.161Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T12:21:16Z | event | event Unhealthy x12 on Pod/catalog-indexer-6f6b545fdb-rpmzl,catalog-indexer-6f6b545fdb-wv8gh: Readiness probe failed: Get "http://10.244.1.66:8080/hea… | O4 |
| 2026-10-13T12:21:28Z | event | event FailedGetResourceMetric x7 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: unable to get metrics for resource cpu: no metrics re… | O4 |
| 2026-10-13T12:21:28Z | event | event FailedComputeMetricsReplicas x7 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T12:21:43Z | event | event FailedGetResourceMetric x12 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods migh… | O4 |
| 2026-10-13T12:21:43Z | event | event FailedComputeMetricsReplicas x12 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resour… | O4 |
| 2026-10-13T12:26:45Z | event | event Unhealthy x25 on Pod/recommendations-54c5f6ddff-7fvrl,recommendations-54c5f6ddff-8nwmm: Readiness probe failed: Get "http://10.244.1.100:8080/he… | O4 |
| 2026-10-13T12:42:37Z | event | event Unhealthy x98 on Pod/checkout-55f8c5b4bc-6ssw7,checkout-55f8c5b4bc-bqhj9: Readiness probe failed: Get "http://10.244.1.91:8080/readyz": dial tcp… | O4 |
| 2026-10-13T12:42:38Z | event | event Unhealthy x54 on Pod/inventory-5577665986-4q7mj,inventory-5577665986-9g7mx: Readiness probe failed: Get "http://10.244.1.106:8080/healthz": dial… | O4 |
| 2026-10-13T12:42:38Z | event | event Unhealthy x50 on Pod/edge-66978949cf-2m5mj,edge-66978949cf-g8mnj: Readiness probe failed: Get "http://10.244.1.97:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x9 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (… | O4 |
| 2026-10-13T12:45:59Z | event | event Unhealthy x5 on Pod/inventory-6dcd8d4f55-vb8z7: Liveness probe failed: Get "http://10.244.1.65:8080/healthz": context deadline exceeded (C… | O4 |
| 2026-10-13T12:46:36Z | event | event Unhealthy x1 on Pod/inventory-6dcd8d4f55-vb8z7: Liveness probe failed: Get "http://10.244.1.65:8080/healthz": dial tcp 10.244.1.65:8080: c… | O4 |
| 2026-10-13T12:47:02Z | event | event Unhealthy x1 on Pod/inventory-6dcd8d4f55-vb8z7: Readiness probe failed: Get "http://10.244.1.65:8080/healthz": read tcp 10.244.1.1:52866->… | O4 |
| 2026-10-13T12:50:07Z | event | event Unhealthy x1 on Pod/checkout-6cc8cb7b8c-9kcll: Readiness probe failed: Get "http://10.244.1.60:8080/readyz": context deadline exceeded (C… | O4 |
| 2026-10-13T12:50:12Z | event | event Unhealthy x2 on Pod/catalog-indexer-6f6b545fdb-rpmzl,catalog-indexer-6f6b545fdb-wv8gh: Liveness probe failed: Get "http://10.244.1.66:8080/healt… | O4 |
| 2026-10-13T12:54:38Z | event | event Unhealthy x3 on Pod/checkout-7d6bdccdc8-7qz6f,checkout-7d6bdccdc8-r6c2x: Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": co… | O4 |
| 2026-10-13T12:54:42Z | event | event Unhealthy x11 on Pod/checkout-7d6bdccdc8-7qz6f,checkout-7d6bdccdc8-r6c2x: Liveness probe failed: Get "http://10.244.1.82:8080/healthz?deep=1": d… | O4 |
| 2026-10-13T12:55:16Z | event | event BackOff x17 on Pod/checkout-7d6bdccdc8-wd72m: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-wd72m_shop(41dd06… | O4 |
| 2026-10-13T12:55:16Z | event | event BackOff x3 on Pod/checkout-7d6bdccdc8-7qz6f: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-7qz6f_shop(0d8ee6… | O4 |
| 2026-10-13T12:55:17Z | event | event BackOff x18 on Pod/checkout-7d6bdccdc8-r6c2x: Back-off restarting failed container checkout in pod checkout-7d6bdccdc8-r6c2x_shop(94ba00… | O4 |
| 2026-10-13T13:03:17Z | event | event Unhealthy x33 on Pod/edge-66978949cf-2m5mj,edge-66978949cf-g8mnj: Readiness probe failed: Get "http://10.244.1.97:8080/healthz": context deadlin… | O4 |
| 2026-10-13T13:03:20Z | event | event Unhealthy x27 on Pod/edge-66978949cf-2m5mj,edge-66978949cf-g8mnj: Liveness probe failed: Get "http://10.244.1.97:8080/healthz": context deadline… | O4 |
| 2026-10-13T13:03:30Z | onset | edge cpu_throttled_ratio on 2/3 series increase: 0.0 → 0.717297 | O7 |
| 2026-10-13T13:04:15Z | onset | edge container_restarts on 3/3 series increase: 0.0 → 2.0 | O7 |
| 2026-10-13T13:04:53Z | event | event Unhealthy x1 on Pod/edge-66978949cf-g8mnj: Readiness probe failed: Get "http://10.244.1.98:8080/healthz": read tcp 10.244.1.1:49114->… | O4 |
| 2026-10-13T13:07:31Z | event | event BackOff x13 on Pod/edge-66978949cf-2m5mj: Back-off restarting failed container edge in pod edge-66978949cf-2m5mj_shop(2c4af26d-274d-… | O4 |
| 2026-10-13T13:09:15Z | event | event BackOff x4 on Pod/edge-66978949cf-g8mnj: Back-off restarting failed container edge in pod edge-66978949cf-g8mnj_shop(f7cb0755-f2ff-… | O4 |
| 2026-10-13T13:11:30+00:00 | change | deployment/edge modified: spec.replicas 3 → 2 (by kubectl-client-side-apply) | O2 |
| 2026-10-13T13:11:30+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (since reverted) (by kubectl-roll… | O2 |

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H2 | 0.39 | cause | version_skew | active | +4/−0 | kubernetes, prometheus | Newly created workload pricing-legacy serves traffic with different code |
| H5 | 0.39 | cause | version_skew | active | +4/−0 | kubernetes, prometheus | Service pricing mixes versions of its backend |
| H4 | 0.11 | cause | capacity | active | +5/−0 | kubernetes, prometheus | Capacity of edge was reduced (spec.replicas 3->2) |
| H3 | 0.05 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap checkout-config change (data.DB_POOL_SIZE 30->4) broke a dependent service |
| H1 | 0.03 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap feature-flags change (data.flags.json {"smart_routing": false, "new_checkout_ui": true} ->{"smart_routing": tr… |

<details><summary>Evidence for/against other hypotheses</summary>

- H4 supports (weak, O7/prometheus): `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 76, "from": "2026-10-13T13:04:45Z", "to…` — 'timeout' observed
- H4 supports (weak, O6/prometheus): `1\u2581\u2582", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "pricing-legacy-79659d…` — 'throttl' observed
- H4 supports (weak, O8/prometheus): `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 76, "from": "2026-10-13T13:04:45Z", "to…` — 'timeout' observed
- H1 supports (weak, O2/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "30", "new": "4", "in_effect": true}], "a…` — 'pool' observed
- H3 supports (moderate, O2/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "30", "new": "4", "in_effect": true}], "a…` — 'pool' observed near checkout-config
- H1 supports (weak, O4/kubernetes): `": dial tcp 10.244.1.125:8080: connect: connection refused", "count": 2, "first_seen": "2026-10-13T1…` — 'connection' observed
- H3 supports (weak, O4/kubernetes): `": dial tcp 10.244.1.125:8080: connect: connection refused", "count": 2, "first_seen": "2026-10-13T1…` — 'connection' observed
- H4 supports (moderate, O4/kubernetes): `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 33, "fir…` — 'timeout' observed near edge
- H4 supports (weak, O9/prometheus): `04148, "value_after": 0.028263}}], "cpu_throttled_ratio": [{"labels": {"pod": "pricing-95c99775f-8v9…` — 'throttl' observed
- H5 supports (moderate, O2/kubernetes): `, "namespace": "shop", "name": "pricing-legacy", "change": "created", "fields": [], "actor": {"manag…` — 'legacy' observed near pricing
- H5 supports (moderate, O3/kubernetes): `2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 'shop:1.4.0']"], "work…` — 'legacy' observed near pricing
- H5 supports (moderate, O4/kubernetes): `y", "kind": "Pod", "objects": ["pricing-legacy-79659db7cf-2lnp8"], "message": "Readiness probe faile…` — 'legacy' observed near pricing
- H5 supports (moderate, O6/prometheus): `amespace": "shop", "workload": "pricing-legacy", "window_minutes": 30, "step_seconds": 15, "signals"…` — 'legacy' observed near pricing

</details>

## Uncertainty

- Baseline rule reasoner: causal links are keyword-based, verify manually.
- 12 evidence claim(s) were rejected by the grounding check (quote not found in the cited observation); they did not affect the conclusion.

## Suggested remediation (not executed — the agent is read-only)

- Review and revert the implicated change if confirmed.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +0 accepted / 0 rejected; new hypotheses []
  - `active_alerts` {} — what is alerting and since when → O1
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O2
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: continue; evidence +12 accepted / 0 rejected; new hypotheses ['H1', 'H2', 'H3', 'H4']
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O5
  - `workload_metrics` {"namespace": "shop", "workload": "pricing-legacy", "minutes": 30} — test H2 → O6
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O7
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — test H4 → O8
  - posteriors: H1=0.04, H2=0.66, H3=0.08, H4=0.17, unexplained=0.05

**Round 2** — decision: continue; evidence +5 accepted / 12 rejected; new hypotheses ['H5']
  - `workload_metrics` {"namespace": "shop", "workload": "pricing", "minutes": 30} — test H5 → O9
  - posteriors: H1=0.03, H2=0.39, H3=0.05, H4=0.11, H5=0.39, unexplained=0.03

**Round 3** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.03, H2=0.39, H3=0.05, H4=0.11, H5=0.39, unexplained=0.03

**Round 4** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.03, H2=0.39, H3=0.05, H4=0.11, H5=0.39, unexplained=0.03

Stop reason: no new evidence for two rounds

</details>