# kubesleuth evaluation, 20261013-093754

Run on a GitHub-hosted runner (ubuntu-latest), kind v0.29.0, commit 394f2c6249118564d6a9f418d925d5bf1d22255f, workflow run https://github.com/Suryanshu24052006/kubesleuth/actions/runs/38375961047

**llm:google_genai:gemini-3.8-flash**: correct 0/1, partial 0, inconclusive 1, wrong 0  

| Scenario | Reasoner | Alert fired | Verdict | Confidence | Evidence sources | Rounds | Tool calls | Rejected claims | Time (s) | Tokens | Root cause given by the agent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [github-conn-saturation](github-conn-saturation.llm-google_genai-gemini-3.8-flash.md) | llm:google_genai:gemini-3.8-flash | ShopEdgeHigh5xxRate | **inconclusive** | inconclusive (0.149) |  | 3 | 8 | 0 | 1852.8 | 62825 | Increasing DB_POOL_SIZE in checkout-config from 4 to 30 caused checkout pods to exceed PostgreSQL max connections, resulting in 5xx errors. |
