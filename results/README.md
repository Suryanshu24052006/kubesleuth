# Live results

Every number here comes from a real run of the `live-eval` GitHub Actions workflow. Each run:
- builds a fresh kind cluster on a GitHub-hosted machine (4 vCPU, 16 GB) with `make up`;
- runs the security demo against the live cluster;
- then, for each scenario, resets the shop, injects the failure, waits for Alertmanager, and lets the agent
  investigate.

The rule-based baseline and the LLM agent investigate **the same live incident**, and each RCA is scored
against the scenario's ground truth. Nothing here is hand-edited.

| Run | Date | What changed before it | Baseline | LLM | Security demo |
|---|---|---|---|---|---|
| [run 1](live/2026-10-13-run1/summary.md) | 13 Oct 2026 | first complete run | **3/6 correct**, 1 partial | **2/5 correct**, 2 partial (1 not run: quota) | all checks passed ([output](live/2026-10-13-run1/security-demo.txt)) |
| [run 2](live/2026-10-13-run2/summary.md) | 13 Oct 2026 | the 8 fixes listed below | **4/6 correct**, 0 wrong | **4/6 correct**, 1 partial, 0 wrong | all checks passed ([output](live/2026-10-13-run2/security-demo.txt)) |

## Run 2 (after the fixes), scenario by scenario

| Scenario (real post-mortem) | Baseline | LLM agent |
|---|---|---|
| AWS EBS 2012: latent memory leak | ✅ correct ([report](live/2026-10-13-run2/aws-ebs-2012-latent-leak.rules.md)) | ⚠️ inconclusive: chased containerd errors caused by the harness restarting many workloads at once ([report](live/2026-10-13-run2/aws-ebs-2012-latent-leak.llm-google_genai-gemini-3.5-flash.md)) |
| AWS S3 2017: mistyped capacity removal | ✅ correct ([report](live/2026-10-13-run2/aws-s3-2017-capacity-removal.rules.md)) | ✅ correct, confidence high (0.99) ([report](live/2026-10-13-run2/aws-s3-2017-capacity-removal.llm-google_genai-gemini-3.5-flash.md)) |
| Chef 2014: aggressive health checks | ⚠️ inconclusive ([report](live/2026-10-13-run2/chef-2014-healthcheck-timeouts.rules.md)) | ✅ correct, high (0.96): the `/healthz?deep=1` probe with failureThreshold 1 ([report](live/2026-10-13-run2/chef-2014-healthcheck-timeouts.llm-google_genai-gemini-3.5-flash.md)) |
| Cloudflare 2019: regex CPU exhaustion | ⚠️ inconclusive: found the WAF ConfigMap change but could not confirm it ([report](live/2026-10-13-run2/cloudflare-2019-waf-regex.rules.md)) | ✅ correct, high (0.89), evidence from 3 sources ([report](live/2026-10-13-run2/cloudflare-2019-waf-regex.llm-google_genai-gemini-3.5-flash.md)) |
| GitHub: DB connection saturation | ✅ correct ([report](live/2026-10-13-run2/github-conn-saturation.rules.md)) | 🟡 partial: its narrative named DB_POOL_SIZE 4→30, but its top-scored hypothesis blamed the victim, inventory (0.54 vs 0.45) ([report](live/2026-10-13-run2/github-conn-saturation.llm-google_genai-gemini-3.5-flash.md)) |
| Knight Capital 2012: stale version + flag | ✅ correct ([report](live/2026-10-13-run2/knight-2012-stale-version-flag.rules.md)) | ✅ correct, high (0.99), 3 sources ([report](live/2026-10-13-run2/knight-2012-stale-version-flag.llm-google_genai-gemini-3.5-flash.md)) |

**Together, at least one of the two approaches found the root cause in all 6 scenarios**, and neither
named a wrong cause. Model note: today's free quota for the regular Flash models was already used, so
the LLM ran almost entirely on the lightest model, `gemini-3.5-flash-lite`. Every report lists the models
it actually used.

What run 2 still shows:
- The LLM is strongest where the cause has to be connected across sources (probe settings, regex rule,
  stale version). The baseline is strongest where one recent change explains everything.
- When a victim and its cause score close together (GitHub scenario), the ledger can still crown the victim.
  Next improvement: let evidence of the form "fails because upstream X failed" move belief to X.
- The harness itself added noise: resetting between scenarios restarted four deployments at once.
  Now fixed: resets only restart what a scenario changed.

## Run 1, scenario by scenario

| Scenario (real post-mortem) | Baseline | LLM (Gemini Flash, free tier) |
|---|---|---|
| AWS EBS 2012: latent memory leak | ✅ correct ([report](live/2026-10-13-run1/aws-ebs-2012-latent-leak.rules.md)) | ⚠️ inconclusive. Its narrative was right ("telemetry-collector renamed…"), but its evidence was lost to quota errors ([report](live/2026-10-13-run1/aws-ebs-2012-latent-leak.llm-google_genai-gemini-3.5-flash.md)) |
| AWS S3 2017: mistyped capacity removal | ✅ correct ([report](live/2026-10-13-run1/aws-s3-2017-capacity-removal.rules.md)) | 🟡 partial: blamed a real containerd outage on the overloaded runner ([report](live/2026-10-13-run1/aws-s3-2017-capacity-removal.llm-google_genai-gemini-3.5-flash.md)) |
| Chef 2014: aggressive health checks | 🟡 partial ([report](live/2026-10-13-run1/chef-2014-healthcheck-timeouts.rules.md)) | ✅ correct: the deep liveness probe with failureThreshold 1 ([report](live/2026-10-13-run1/chef-2014-healthcheck-timeouts.llm-google_genai-gemini-3.5-flash.md)) |
| Cloudflare 2019: regex CPU exhaustion | ❌ wrong: blamed a change left over from the previous scenario ([report](live/2026-10-13-run1/cloudflare-2019-waf-regex.rules.md)) | ✅ correct: named the exact WAF rule, posterior 0.91 ([report](live/2026-10-13-run1/cloudflare-2019-waf-regex.llm-google_genai-gemini-3.5-flash.md)) |
| GitHub: DB connection saturation | ⚠️ inconclusive ([report](live/2026-10-13-run1/github-conn-saturation.rules.md)) | 🟡 partial: found the failing DB connections but stopped at the victim ([report](live/2026-10-13-run1/github-conn-saturation.llm-google_genai-gemini-3.5-flash.md)) |
| Knight Capital 2012: stale version + flag | ✅ correct ([report](live/2026-10-13-run1/knight-2012-stale-version-flag.rules.md)) | not run: every free Gemini model had used its daily quota |

The two approaches fail differently. The baseline is fast and literal: good when one recent change
explains everything, misled by noise. The LLM connects mechanisms across sources (it named the exact
Cloudflare WAF rule and the probe settings), but it depends on a reliable model API.

## Problems the live runs exposed, and what I changed

| # | Problem seen on the live cluster | Fix | Test |
|---|---|---|---|
| 1 | Real tool results are far larger than the recorded test incident. The broker trimmed long lists by appending a "…N more omitted" string, and the agent's timeline crashed on it. | Lists are trimmed without markers; recent changes come newest-first so trimming keeps the latest ones; the agent ignores malformed items. | `agent/tests/test_large_results.py` |
| 2 | The eval's `kubectl port-forward` tunnels to the broker died silently, so no investigation reached the cluster. | Tunnels health-check before every use, restart themselves, and log to the run output. | exercised by every live run |
| 3 | `gemini-2.5-flash` had been retired. The agent kept going and reported "inconclusive", hiding a configuration error. | An unusable model (404, bad key) now stops the run with a clear error. | `test_unusable_model_fails_fast_instead_of_inconclusive` |
| 4 | The free tier allows about 20 requests/day and as few as 5/minute per model, and the agent used about 20 calls per investigation. | One model call per round (about 6 per investigation); per-minute limits and 503 overloads are retried with backoff; when a model's daily quota runs out the agent continues on the next model, and reports list every model used. | `test_llm_reasoner_one_call_per_round`, `test_daily_quota_falls_back_to_next_model`, `test_overloaded_provider_is_retried_then_switched` |
| 5 | Models returned near-miss JSON ("supporting", missing fields) or ran out of output tokens mid-answer, wasting calls. | Near-misses are normalised (evidence still has to pass the verbatim-quote check), output limit raised, short quotes requested. | `test_llm_reasoner_one_call_per_round` |
| 6 | **Broker bug:** `kubectl scale` was credited to `kube-controller-manager`, because the controller's later status writes hid the human who made the change. | Status-subresource writes are ignored when deciding who changed something. | `test_journal_credits_the_human_not_the_status_writer` |
| 7 | Changes from earlier scenarios, already reverted, misled the baseline (Cloudflare case). | Every change now says whether it is **still in effect**; prompts and the baseline treat reverted and controller-made changes as unlikely causes. | `test_journal_marks_reverted_changes` |
| 8 | During the S3 scenario the 4-vCPU runner was so loaded that containerd refused connections, a real but unintended fault that the LLM (reasonably) blamed. | Edge autoscaler capped at 3 replicas to leave headroom. | next live run |

Raw logs, diagnostics and every report of every run are on the
[`ci-output`](https://github.com/Suryanshu24052006/kubesleuth/tree/ci-output) branch.
