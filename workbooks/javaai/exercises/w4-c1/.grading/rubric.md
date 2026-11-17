# Rubric: javaai/w4-c1 Tutor agent service on Cloud Run: ID-token auth, scoped tools, guardrails
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Auth correctness | 10 | Algorithms pinned to RS256, audience and issuer verified, required claims, 401 vs 403 distinguished, auth as a FastAPI dependency so the model is never reached; mentions that production verifies against Google's JWKS (google-auth) with key caching. |
| 3 | Tool boundary design | 15 | Allow-list in code, write tool absent from the agent entirely, session-bound arguments (the model never chooses learner or course), validated arguments, errors returned to the model; explains the confused-deputy risk of letting the model pick learner_id. |
| 4 | Guardrails | 10 | Before-model refusal without a model call, after-model leak check, bounded loop with a fallback; ANSWER.md maps each to ADK (before_model_callback, after_model_callback, tool filter / McpToolset tool_filter) and explains why the prompt alone cannot enforce them. |
| 5 | Production judgement | 10 | Cloud Run no-allow-unauthenticated + roles/run.invoker for the caller SA as the first layer, in-app checks as the second; limits of a keyword topic guard (false refusals; a classifier or Model Armor later); logging of refusals and withheld replies as metrics; cost of each extra model call. |
| 6 | Code quality | 5 | Small functions, typed Pydantic arg models, no global mutable state added, readable loop. |
Total: 100
