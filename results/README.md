# Live results

Every number here comes from a real run of the `live-eval` GitHub Actions workflow. Each run:
- builds a fresh kind cluster on a GitHub-hosted machine (4 vCPU, 16 GB) with `make up`;
- runs the security demo against the live cluster;
- then, for each scenario, resets the shop, injects the failure, waits for Alertmanager, and lets two
  reasoners investigate **the same live incident**: the rule-based baseline and the LLM agent (Gemini, free tier).

All three runs are graded by the same strict scorer ([`eval/score.py`](../eval/score.py)). A verdict is
**correct** only if the root-cause statement names the right component **and** the actual mechanism, and the
winning hypothesis does not blame a victim. Nothing in the report except the conclusion counts.

## Summary over 3 runs (36 investigations)

| | Baseline (rules) | LLM agent | Either one |
|---|---|---|---|
| Correct root cause | **10 / 18** (56%) | **8 / 17** (47%) | **15 / 18** (83%) |
| Partially right | 0 | 4 | |
| Wrong cause | 2 (both in run 1) | 3 | |
| "Inconclusive" (declined to guess) | 6 | 2 | |
| Security demo on the live cluster | **passed in all 3 runs** | | |

One LLM investigation (run 1, Knight) could not run because the free daily quota was used up.

| Run | Baseline | LLM | Either | Security demo |
|---|---|---|---|---|
| [run 1](live/2026-10-13-run1/summary.md), 13 Oct | 3 correct, 2 wrong, 1 inconclusive | 2 correct, 1 partial, 1 wrong, 1 inconclusive, 1 not run | 5/6 | [passed](live/2026-10-13-run1/security-demo.txt) |
| [run 2](live/2026-10-13-run2/summary.md), 13 Oct, after fixing what run 1 exposed | 4 correct, 2 inconclusive | 4 correct, 1 partial, 1 inconclusive | **6/6** | [passed](live/2026-10-13-run2/security-demo.txt) |
| [run 3](live/2026-10-14-run3/summary.md), 14 Oct, fresh quota, quieter resets | 3 correct, 3 inconclusive | 2 correct, 2 partial, 2 wrong | 4/6 | [passed](live/2026-10-14-run3/security-demo.txt) |

## Scenario by scenario: the two reasoners are complementary

| Scenario (real post-mortem) | Baseline correct | LLM correct | What happens |
|---|---|---|---|
| Knight Capital 2012: stale version + reused flag | **3/3** | **2/2** | Both find the forgotten `pricing-legacy` deployment behind the Service. |
| AWS S3 2017: mistyped capacity removal | **3/3** | 1/3 | One recent human `kubectl scale` explains everything, so the baseline nails it. The LLM sometimes chases real side effects (Postgres connections, an overloaded node). |
| AWS EBS 2012: latent memory leak | **3/3** | 0/3 | The baseline links the deleted `telemetry-collector` Service directly. The LLM gets distracted by node and containerd noise on the small runner (its narrative was right once, in run 1, but its evidence was lost to quota errors). |
| Chef 2014: aggressive health checks | 0/3 | **3/3** | The baseline sees the probe change but cannot weigh it against the real DB latency. The LLM explains the amplifier: a deep `/healthz?deep=1` probe with a 1 s timeout and failureThreshold 1. |
| Cloudflare 2019: regex CPU exhaustion | 0/3 | **2/3** | The baseline finds the WAF ConfigMap change but cannot confirm it. The LLM names the exact backtracking rule (posterior 0.89–0.91). |
| GitHub: DB connection saturation | 1/3 | 0/3 (3 partial) | The hardest one: the failing service (inventory) is a victim. The LLM always finds the exhausted DB connections, but crowns the victim instead of the `DB_POOL_SIZE 4→30` change. |

**Takeaway.** The baseline wins when one recent change explains everything. The LLM wins when the cause has to
be *reasoned out* across sources: an amplifier, a specific rule, a mechanism. Combined, they found the root
cause in 15 of 18 investigations. The obvious next step is a hybrid: seed the LLM's ledger with the
baseline's change-based hypotheses, and let evidence of the form "X fails because upstream Y failed" move
belief from victim X to cause Y.

Results vary between runs (for example LLM Cloudflare: correct, correct, wrong) because the LLM is
non-deterministic, the free tier forces model switching mid-investigation, and a 4-vCPU runner is a noisy
place to run a 30-pod cluster. Every report lists the models it actually used.

## How the grading changed (transparency)

While reviewing run 3 I found the first scorer was too lenient. It matched keywords anywhere in the report
and accepted a generic component name, so an answer blaming the victim (inventory) was marked correct
because its component field said "checkout". The scorer now only reads the conclusion and requires the
mechanism (tests in [`agent/tests/test_score.py`](../agent/tests/test_score.py)). All three runs were
re-graded with [`eval/rescore.py`](../eval/rescore.py); the investigations themselves were not rerun or
changed. Under the old scorer, run 2 read "LLM 4/6" and run 3 "LLM 3/6".

## Problems the live runs exposed, and what I changed

| # | Problem seen on the live cluster | Fix | Test |
|---|---|---|---|
| 1 | Real tool results are far larger than the recorded test incident. The broker trimmed long lists by appending a "…N more omitted" string, and the agent's timeline crashed on it. | Lists are trimmed without markers; recent changes come newest-first so trimming keeps the latest ones; the agent ignores malformed items. | `agent/tests/test_large_results.py` |
| 2 | The eval's `kubectl port-forward` tunnels to the broker died silently, so no investigation reached the cluster. | Tunnels health-check before every use, restart themselves, and log to the run output. | exercised by every live run |
| 3 | `gemini-2.5-flash` had been retired. The agent kept going and reported "inconclusive", hiding a configuration error. | An unusable model (404, bad key) now stops the run with a clear error. | `test_unusable_model_fails_fast_instead_of_inconclusive` |
| 4 | The free tier allows about 20 requests/day and as few as 5/minute per model, and the agent used about 20 calls per investigation. | One model call per round (about 6 per investigation); per-minute limits and 503 overloads are retried with backoff; when a model's daily quota runs out the agent continues on the next model. | `test_llm_reasoner_one_call_per_round`, `test_daily_quota_falls_back_to_next_model`, `test_overloaded_provider_is_retried_then_switched` |
| 5 | Models returned near-miss JSON ("supporting", missing fields) or ran out of output tokens mid-answer. | Near-misses are normalised (evidence still has to pass the verbatim-quote check), output limit raised, short quotes requested. | `test_llm_reasoner_one_call_per_round` |
| 6 | **Broker bug:** `kubectl scale` was credited to `kube-controller-manager`, because the controller's later status writes hid the human who made the change. | Status-subresource writes are ignored when deciding who changed something. | `test_journal_credits_the_human_not_the_status_writer` |
| 7 | Changes from earlier scenarios, already reverted, misled the baseline. | Every change now says whether it is **still in effect**; prompts and the baseline treat reverted and controller-made changes as unlikely causes. | `test_journal_marks_reverted_changes` |
| 8 | The 4-vCPU runner got so loaded that containerd refused connections, a real but unintended fault. | Edge autoscaler capped at 3 replicas; resets between scenarios restart only what a scenario changed. | runs 2 and 3 |
| 9 | The first scorer credited victim-blaming answers (see above). | Strict scorer; all runs re-graded. | `agent/tests/test_score.py` |

Raw logs, diagnostics and every report of every run are on the
[`ci-output`](https://github.com/Suryanshu24052006/kubesleuth/tree/ci-output) branch.
