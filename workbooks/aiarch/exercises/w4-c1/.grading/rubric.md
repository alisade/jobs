# Rubric: aiarch/w4-c1 On-behalf-of token exchange
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Security of validation | 15 | Algorithm allow-list, kid lookup, audience and issuer always checked, issued token checked for sub, aud, scope and actor before use, no passthrough. |
| 3 | Scope and cache design | 10 | Scope narrowed to user and target; cache key includes user, target and scopes; refresh before expiry. |
| 4 | Code quality | 5 | One decode helper, clear error messages, no duplicated checks. |
| 5 | ANSWER.md | 15 | Complete token path with issuer, audience, subject and actor for each token; correct AgentCore Identity mapping; IdP support caveat (Entra JWT-bearer). |
Total: 100
