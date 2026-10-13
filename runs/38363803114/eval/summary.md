# kubesleuth evaluation, 20261013-074959

Run on a GitHub-hosted runner (ubuntu-latest), kind v0.29.0, commit aaa73940bc4ae429f18958e9f3b775b7bcc7912e, workflow run https://github.com/Suryanshu24052006/kubesleuth/actions/runs/38363803114

**rules**: correct 0/6, partial 0, inconclusive 0, wrong 0, errors 6  
**llm**: correct 0/6, partial 0, inconclusive 0, wrong 0, errors 6  

| Scenario | Reasoner | Alert fired | Verdict | Confidence | Evidence sources | Rounds | Tool calls | Rejected claims | Time (s) | Tokens | Root cause given by the agent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aws-ebs-2012-latent-leak | rules | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| aws-ebs-2012-latent-leak | llm | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| aws-s3-2017-capacity-removal | rules | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| aws-s3-2017-capacity-removal | llm | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| chef-2014-healthcheck-timeouts | rules | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| chef-2014-healthcheck-timeouts | llm | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| cloudflare-2019-waf-regex | rules | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| cloudflare-2019-waf-regex | llm | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| github-conn-saturation | rules | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| github-conn-saturation | llm | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| knight-2012-stale-version-flag | rules | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
| knight-2012-stale-version-flag | llm | no | **error** | None (None) |  | None | None | None | None | 0 | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) |
