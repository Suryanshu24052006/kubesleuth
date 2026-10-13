# RCA: Newly created workload pricing-legacy serves traffic with different code

**Incident:** Checkout errors jumped to roughly a third of requests a few minutes ago.  
**Namespace:** `shop` · **Investigation:** `20261013-115930-61b121` · **Reasoner:** `rules` · 4 rounds, 9 tool calls, 1.0s

## Root cause

Newly created workload pricing-legacy serves traffic with different code

*Hypothesis H2 · component `pricing-legacy` · category `version_skew`*

**Confidence: LOW** (posterior 0.46). Low: the leading explanation is plausible but not demonstrated.

## Causal chain

1. 'legacy' observed near pricing-legacy: amespace": "shop", "workload": "pricing-legacy", "window_minutes": 30, "step_sec (O6)
2. 'legacy' observed near pricing-legacy: , "namespace": "shop", "name": "pricing-legacy", "change": "created", "fields":  (O2)
3. 'legacy' observed near pricing-legacy: 2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 's (O3)
4. 'legacy' observed near pricing-legacy: y", "kind": "Pod", "objects": ["pricing-legacy-79659db7cf-jl4c4"], "message": "R (O4)
5. 'legacy' observed near pricing-legacy: _pod_rps": [{"labels": {"pod": "pricing-legacy-79659db7cf-jl4c4"}, "points": 3,  (O9)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O6 | prometheus | moderate (+1.2) | `amespace": "shop", "workload": "pricing-legacy", "window_minutes": 30, "step_seconds": 15, "signals": {"cp` | 'legacy' observed near pricing-legacy |
| ✅ O2 | kubernetes | moderate (+1.2) | `, "namespace": "shop", "name": "pricing-legacy", "change": "created", "fields": [], "actor": {"manager": "` | 'legacy' observed near pricing-legacy |
| ✅ O3 | kubernetes | moderate (+0.72) | `2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 'shop:1.4.0']"], "workloads"` | 'legacy' observed near pricing-legacy |
| ✅ O4 | kubernetes | moderate (+0.432) | `y", "kind": "Pod", "objects": ["pricing-legacy-79659db7cf-jl4c4"], "message": "Readiness probe failed: Get` | 'legacy' observed near pricing-legacy |
| ✅ O9 | prometheus | moderate (+0.72) | `_pod_rps": [{"labels": {"pod": "pricing-legacy-79659db7cf-jl4c4"}, "points": 3, "from": "2026-10-13T11:59:` | 'legacy' observed near pricing-legacy |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-13T10:34:40.513Z | alert | alert Watchdog fired (none) | O1 |
| 2026-10-13T10:55:00Z | event | event Unhealthy x61 on Pod/inventory-5f7599564b-7mm8z,inventory-5f7599564b-9g5g6: Readiness probe failed: Get "http://10.244.1.105:8080/healthz": dial… | O4 |
| 2026-10-13T10:55:00Z | event | event Unhealthy x89 on Pod/checkout-5b5779f467-5lksr,checkout-5b5779f467-8xhd7: Readiness probe failed: Get "http://10.244.1.123:8080/readyz": dial tc… | O4 |
| 2026-10-13T10:55:24Z | event | event FailedGetResourceMetric x7 on HorizontalPodAutoscaler/edge: failed to get cpu utilization: did not receive metrics for targeted pods (pods might… | O4 |
| 2026-10-13T10:55:24Z | event | event FailedComputeMetricsReplicas x7 on HorizontalPodAutoscaler/edge: invalid metrics (1 invalid out of 1), first error is: failed to get cpu resourc… | O4 |
| 2026-10-13T10:58:23Z | event | event Unhealthy x16 on Pod/inventory-5f7599564b-7mm8z,inventory-5f7599564b-svtzs: Readiness probe failed: Get "http://10.244.1.105:8080/healthz": cont… | O4 |
| 2026-10-13T11:01:56Z | event | event Unhealthy x9 on Pod/catalog-indexer-6f6b545fdb-7qmw8,catalog-indexer-6f6b545fdb-jrh2l: Readiness probe failed: Get "http://10.244.1.66:8080/heal… | O4 |
| 2026-10-13T11:01:57Z | event | event Unhealthy x19 on Pod/recommendations-55b5fd5477-6lbkr,recommendations-55b5fd5477-cdtzd: Readiness probe failed: Get "http://10.244.1.88:8080/hea… | O4 |
| 2026-10-13T11:01:57Z | event | event Unhealthy x40 on Pod/edge-7999f79dc7-km984,edge-7999f79dc7-rl6dx: Readiness probe failed: Get "http://10.244.1.79:8080/healthz": dial tcp 10.244… | O4 |
| 2026-10-13T11:02:03Z | event | event Unhealthy x2 on Pod/catalog-indexer-6f6b545fdb-7qmw8,catalog-indexer-6f6b545fdb-jrh2l: Liveness probe failed: Get "http://10.244.1.66:8080/healt… | O4 |
| 2026-10-13T11:06:31Z | event | event Unhealthy x3 on Pod/checkout-69d8947794-29kkk,checkout-69d8947794-5qm4v: Liveness probe failed: Get "http://10.244.1.83:8080/healthz?deep=1": co… | O4 |
| 2026-10-13T11:06:35Z | event | event Unhealthy x11 on Pod/checkout-69d8947794-29kkk,checkout-69d8947794-5qm4v: Liveness probe failed: Get "http://10.244.1.83:8080/healthz?deep=1": d… | O4 |
| 2026-10-13T11:07:09Z | event | event BackOff x3 on Pod/checkout-69d8947794-29kkk: Back-off restarting failed container checkout in pod checkout-69d8947794-29kkk_shop(1c3330… | O4 |
| 2026-10-13T11:07:09Z | event | event BackOff x3 on Pod/checkout-69d8947794-5qm4v: Back-off restarting failed container checkout in pod checkout-69d8947794-5qm4v_shop(8bb9a3… | O4 |
| 2026-10-13T11:07:11Z | event | event BackOff x3 on Pod/checkout-69d8947794-j8gmg: Back-off restarting failed container checkout in pod checkout-69d8947794-j8gmg_shop(615460… | O4 |
| 2026-10-13T11:14:24Z | event | event Unhealthy x110 on Pod/edge-f647cd7c4-fj7vm,edge-f647cd7c4-jpqfk: Liveness probe failed: Get "http://10.244.1.98:8080/healthz": context deadline … | O4 |
| 2026-10-13T11:14:26Z | event | event Unhealthy x47 on Pod/edge-f647cd7c4-fj7vm,edge-f647cd7c4-jpqfk: Readiness probe failed: Get "http://10.244.1.98:8080/healthz": context deadline … | O4 |
| 2026-10-13T11:14:47Z | event | event Unhealthy x2 on Pod/edge-f647cd7c4-jpqfk,edge-f647cd7c4-mklgr: Liveness probe failed: Get "http://10.244.1.87:8080/healthz": dial tcp 10.244.1.8… | O4 |
| 2026-10-13T11:20:29+00:00 | change | deployment/checkout modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O2 |
| 2026-10-13T11:20:29+00:00 | change | deployment/edge modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O2 |
| 2026-10-13T11:20:29+00:00 | change | deployment/recommendations modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O2 |
| 2026-10-13T11:20:29+00:00 | change | deployment/inventory modified: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O2 |
| 2026-10-13T11:20:29+00:00 | change | rollout/checkout new-revision: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… | O2 |
| 2026-10-13T11:20:29+00:00 | change | rollout/edge new-revision: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… | O2 |
| 2026-10-13T11:20:29+00:00 | change | rollout/inventory new-revision: template.annotations {"kubectl.kubernetes.io/restar… → {"kubectl.kubernetes.io/restar… | O2 |
| 2026-10-13T11:20:38+00:00 | change | deployment/edge modified: spec.replicas 2 → 4 (by kube-controller-manager) | O2 |
| 2026-10-13T11:20:38Z | event | event Unhealthy x1 on Pod/inventory-84986bb8d4-fbppj: Readiness probe failed: Get "http://10.244.1.95:8080/healthz": read tcp 10.244.1.1:47986->… | O4 |
| 2026-10-13T11:20:49+00:00 | change | deployment/edge modified: spec.replicas 4 → 2 (by kube-controller-manager) | O2 |
| 2026-10-13T11:20:56Z | event | event Unhealthy x1 on Pod/inventory-5f7599564b-7mm8z: Liveness probe failed: Get "http://10.244.1.105:8080/healthz": context deadline exceeded (… | O4 |
| 2026-10-13T11:23:49+00:00 | change | configmap/checkout-config modified: data.DB_POOL_SIZE 4 → 30 (by kubectl-patch) | O2 |

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H2 | 0.46 | cause | version_skew | active | +5/−0 | kubernetes, prometheus | Newly created workload pricing-legacy serves traffic with different code |
| H5 | 0.46 | cause | version_skew | active | +5/−0 | kubernetes, prometheus | Service pricing mixes versions of its backend |
| H4 | 0.03 | cause | capacity | active | +5/−0 | kubernetes, prometheus | Capacity of edge was reduced (spec.replicas 4->2) |
| H3 | 0.03 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap checkout-config change (data.DB_POOL_SIZE 30->4) broke a dependent service |
| H1 | 0.01 | cause | configuration | active | +2/−0 | kubernetes | ConfigMap feature-flags change (data.flags.json {"smart_routing": false, "new_checkout_ui": true} ->{"smart_routing": tr… |

<details><summary>Evidence for/against other hypotheses</summary>

- H4 supports (weak, O7/prometheus): `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 121, "from": "2026-10-13T11:29:31Z", "t…` — 'timeout' observed
- H4 supports (weak, O6/prometheus): `6\u2588\u2588", "unit": "cores"}], "cpu_throttled_ratio": [{"labels": {"pod": "pricing-legacy-79659d…` — 'throttl' observed
- H4 supports (weak, O8/prometheus): `abels": {"dep": "checkout", "outcome": "timeout"}, "points": 121, "from": "2026-10-13T11:29:31Z", "t…` — 'timeout' observed
- H1 supports (weak, O2/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "30", "new": "4"}], "actor": {"manager": …` — 'pool' observed
- H3 supports (moderate, O2/kubernetes): `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "30", "new": "4"}], "actor": {"manager": …` — 'pool' observed near checkout-config
- H1 supports (weak, O4/kubernetes): `": dial tcp 10.244.1.128:8080: connect: connection refused", "count": 2, "first_seen": "2026-10-13T1…` — 'connection' observed
- H3 supports (weak, O4/kubernetes): `": dial tcp 10.244.1.128:8080: connect: connection refused", "count": 2, "first_seen": "2026-10-13T1…` — 'connection' observed
- H4 supports (weak, O4/kubernetes): `hz\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)", "count": 16, "fir…` — 'timeout' observed
- H4 supports (weak, O9/prometheus): `02595, "value_after": 0.021342}}], "cpu_throttled_ratio": [{"labels": {"pod": "pricing-95c99775f-5sx…` — 'throttl' observed
- H5 supports (moderate, O9/prometheus): `_pod_rps": [{"labels": {"pod": "pricing-legacy-79659db7cf-jl4c4"}, "points": 3, "from": "2026-10-13T…` — 'legacy' observed near pricing
- H5 supports (moderate, O2/kubernetes): `, "namespace": "shop", "name": "pricing-legacy", "change": "created", "fields": [], "actor": {"manag…` — 'legacy' observed near pricing
- H5 supports (moderate, O3/kubernetes): `2 different workloads (pricing, pricing-legacy) running images ['shop:0.9.7', 'shop:1.4.0']"], "work…` — 'legacy' observed near pricing
- H5 supports (moderate, O4/kubernetes): `y", "kind": "Pod", "objects": ["pricing-legacy-79659db7cf-jl4c4"], "message": "Readiness probe faile…` — 'legacy' observed near pricing
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
  - posteriors: H1=0.05, H2=0.72, H3=0.09, H4=0.09, unexplained=0.06

**Round 2** — decision: continue; evidence +7 accepted / 12 rejected; new hypotheses ['H5']
  - `workload_metrics` {"namespace": "shop", "workload": "pricing", "minutes": 30} — test H5 → O9
  - posteriors: H1=0.01, H2=0.46, H3=0.03, H4=0.03, H5=0.46, unexplained=0.02

**Round 3** — decision: continue; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.01, H2=0.46, H3=0.03, H4=0.03, H5=0.46, unexplained=0.02

**Round 4** — decision: no new evidence for two rounds; evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.01, H2=0.46, H3=0.03, H4=0.03, H5=0.46, unexplained=0.02

Stop reason: no new evidence for two rounds

</details>