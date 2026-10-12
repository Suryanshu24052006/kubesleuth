> Sample output: offline fixture `github-conn-saturation`, **rule-based baseline reasoner** (no LLM). Run `make eval` on the live cluster for LLM results.

# RCA: ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service

**Incident:** The checkout service is experiencing a sudden increase in 5xx errors.  
**Namespace:** `shop` · **Investigation:** `20261012-234815-813923` · **Reasoner:** `rules` · 3 rounds, 8 tool calls, 0.1s

## Root cause

ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service

*Hypothesis H1 · component `configmap/checkout-config` · category `configuration`*

**Confidence: MEDIUM** (posterior 0.77). Medium: well supported, but some evidence is single-source or an alternative is not fully excluded.

## Causal chain

1. 'too many clients' observed: sage": "OperationalError: FATAL: sorry, too many clients already", "count": 12,  (O6)
2. 'pool' observed near checkout-config: odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"}], " (O3)
3. 'too many clients' observed: "<ip>\", port <n> failed: FATAL: sorry, too many clients already", "first_seen": (O8)

## Evidence for the conclusion

| | Source | Strength | Verbatim quote | Why it matters |
|---|---|---|---|---|
| ✅ O6 | jaeger | weak (+0.5) | `sage": "OperationalError: FATAL: sorry, too many clients already", "count": 12, "example_trace_id": "000000000…` | 'too many clients' observed |
| ✅ O3 | kubernetes | moderate (+1.2) | `odified", "fields": [{"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"}], "actor": {"manager": "kub` | 'pool' observed near checkout-config |
| ✅ O8 | loki | weak (+0.5) | `"<ip>\", port <n> failed: FATAL: sorry, too many clients already", "first_seen": "2026-10-12T18:09:35Z", "last…` | 'too many clients' observed |

## Timeline

| Time (UTC) | Kind | Event | Obs |
|---|---|---|---|
| 2026-10-12T17:18:15Z | change | hpa/edge modified: spec.maxReplicas 3 → 4 (by kubectl-edit) | O3 |
| 2026-10-12T18:08:55Z | change | configmap/checkout-config modified: data.DB_POOL_SIZE 4 → 30 (by kubectl-edit) | O3 |
| 2026-10-12T18:09:07Z | change | deployment/checkout modified: template.annotations null → {"kubectl.kubernetes.io/restar… (by kubectl-rollout) | O3 |
| 2026-10-12T18:09:07Z | change | rollout/checkout new-revision: template.annotations null → {"kubectl.kubernetes.io/restar… | O3 |
| 2026-10-12T18:09:35Z | log | first log: stock lookup failed error=OperationalError detail=connection failed: connection to server … (x300) | O8 |
| 2026-10-12T18:09:45Z | event | event Unhealthy x98 on Pod/checkout-7f4d9c8b6-ltql4: Readiness probe failed: HTTP probe failed with statuscode: 503 | O4 |
| 2026-10-12T18:09:45Z | onset | edge error_ratio_5xx increase: 0.002 → 0.4021 | O5 |
| 2026-10-12T18:09:45Z | onset | edge latency_p95_seconds increase: 0.0913 → 0.2276 | O5 |
| 2026-10-12T18:09:45Z | onset | inventory error_ratio_5xx increase: 0.0 → 0.4603 | O7 |
| 2026-10-12T18:09:45Z | onset | inventory errors_by_pod_rps on 4/4 series increase: 0.0 → 2.4112 | O7 |
| 2026-10-12T18:09:45Z | onset | inventory latency_p95_seconds increase: 0.0303 → 0.0932 | O7 |
| 2026-10-12T18:09:45Z | onset | inventory db_errors_rps[OperationalError] increase: 0.0 → 9.7727 | O7 |
| 2026-10-12T18:11:05Z | alert | alert ShopEdgeHigh5xxRate fired (critical) | O1 |
| 2026-10-12T18:13:15Z | event | event Unhealthy x8 on Pod/inventory-xvtq58qwc-nxbqg,inventory-xvtq58qwc-xw95k: Readiness probe failed: Get "http://10.244.1.12:8080/healthz": context … | O4 |

## Observed facts

- edge error_ratio_5xx increase at 2026-10-12T18:09:45Z — `2026-10-12T18:09:45Z` (O5, prometheus)
- inventory error_ratio_5xx increase at 2026-10-12T18:09:45Z — `2026-10-12T18:09:45Z` (O7, prometheus)
- inventory db_errors_rps increase at 2026-10-12T18:09:45Z — `2026-10-12T18:09:45Z` (O7, prometheus)

## Hypotheses considered

| Id | Posterior | Layer | Category | Status | +/− | Sources | Statement |
|---|---|---|---|---|---|---|---|
| H1 | 0.77 | cause | configuration | active | +3/−0 | jaeger, kubernetes, loki | ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service |

## Uncertainty

- Baseline rule reasoner: causal links are keyword-based, verify manually.

## Suggested remediation (not executed — the agent is read-only)

- Review and revert the implicated change if confirmed.

## Security notes

- No suspicious data or blocked actions.

<details><summary>Investigation trace</summary>

**Round 0** — decision: -; evidence +0 accepted / 0 rejected; new hypotheses []
  - `active_alerts` {} — what is alerting and since when → O1
  - `cluster_overview` {"namespace": "shop"} — resource-level health snapshot → O2
  - `recent_changes` {"namespace": "shop", "minutes": 120} — what changed recently → O3
  - `get_events` {"namespace": "shop", "minutes": 60, "warnings_only": true} — recent warning events → O4

**Round 1** — decision: continue; evidence +2 accepted / 0 rejected; new hypotheses ['H1']
  - `workload_metrics` {"namespace": "shop", "workload": "edge", "minutes": 30} — symptom onset → O5
  - `find_traces` {"service": "edge", "minutes": 15} — where do errors originate? → O6
  - posteriors: H1=0.67, unexplained=0.33

**Round 2** — decision: continue; evidence +1 accepted / 0 rejected; new hypotheses []
  - `workload_metrics` {"namespace": "shop", "workload": "inventory", "minutes": 30} — golden signals of inventory → O7
  - `search_logs` {"namespace": "shop", "app": "inventory", "level": "error", "minutes": 30} — errors in inventory → O8
  - posteriors: H1=0.77, unexplained=0.23

**Round 3** — decision: model judged evidence sufficient; H1 p=0.77 (medium); evidence +0 accepted / 0 rejected; new hypotheses []
  - posteriors: H1=0.77, unexplained=0.23

Stop reason: model judged evidence sufficient; H1 p=0.77 (medium)

</details>