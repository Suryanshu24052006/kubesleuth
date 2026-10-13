# kubesleuth evaluation, 20261013-091327

Run on a GitHub-hosted runner (ubuntu-latest), kind v0.29.0, commit 28abd8990a066c7468f1a14dd5010d223faf362d, workflow run https://github.com/Suryanshu24052006/kubesleuth/actions/runs/38373467212

**rules**: correct 1/1, partial 0, inconclusive 0, wrong 0  
**llm:google_genai:gemini-2.5-flash**: correct 0/1, partial 0, inconclusive 1, wrong 0  

| Scenario | Reasoner | Alert fired | Verdict | Confidence | Evidence sources | Rounds | Tool calls | Rejected claims | Time (s) | Tokens | Root cause given by the agent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [github-conn-saturation](github-conn-saturation.rules.md) | rules | ShopEdgeHigh5xxRate | **correct** | medium (0.555) | kubernetes | 2 | 6 | 0 | 0.5 | 0 | ConfigMap checkout-config change (data.DB_POOL_SIZE 4->30) broke a dependent service |
| [github-conn-saturation](github-conn-saturation.llm-google_genai-gemini-2.5-flash.md) | llm:google_genai:gemini-2.5-flash | ShopEdgeHigh5xxRate | **inconclusive** | inconclusive (0.0) |  | 2 | 4 | 0 | 92.3 | 0 | None |
