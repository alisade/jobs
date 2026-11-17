# Rubric: connect/w5-c3 Tune the help desk AI agent against an eval set
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh (several are guards that pass on the baseline) |
| 2 | Tuning method | 20 | Full: changes driven by error analysis (confusions named, e.g. "access" shared by RequestAccess and outage wording; "password" shared by reset and unlock), one lever at a time with metrics, threshold chosen from the misroute/fallback trade-off rather than guessed. Partial: final config good but no evidence of method. Zero: config edited until tests pass with no log. |
| 3 | Generalization and safety | 15 | Full: describes intents by meaning rather than eval wording, holdout gap small, citations required with the reasoning (hallucination becomes a handoff), temperature 0. Partial: passes but descriptions read like pasted test data. |
| 4 | Latency and cost reasoning | 10 | Full: explains prompt-token and topK latency cost, why topK/minScore were set where they are, what this means for Connect's 8 s sync limit and per-contact token cost. Partial: mentions latency only. |
| 5 | Production loop | 10 | Full: concrete plan for the real agent: refresh eval set from transcripts, frozen holdout, A/B with flow Distribute by percentage or alias split, LLM-as-judge or Bedrock RAG evaluation for answers, Lex Test Workbench/Bot Analyzer for NLU, gates in CI. Partial: generic "monitor it". |
Total: 100
