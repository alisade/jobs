# Rubric: connect/w4-c1 Translate legacy IVR scripts into Connect flows
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Semantic fidelity | 15 | Full: holiday vs time-of-day mapped to separate hours resources with the right branch polarity; queue-to uses staffed and check uses available; failed queue attempts continue at the legacy fall-through; menu retries via Loop with maxAttempts; priorities from the mapping, never defaulted. Partial: passes tests but by special-casing the shipped scripts (e.g. hard-coded step numbers). Zero: hard-coded flows. |
| 3 | Fails loudly | 5 | Unknown steps, missing mapping entries and unsupported thresholds throw with a message naming the script and step/node; nothing silently dropped. |
| 4 | Code quality | 10 | Shared emitters for the constructs all three formats share, forward references handled cleanly (reserve ids, resolve aliases for goto/wait/Start), typed, small functions, readable identifiers in the output. |
| 5 | Migration judgement in ANSWER.md | 20 | Full: names at least four things that do not translate 1:1 with the Connect answer for each (in-queue treatment -> customer queue flow; VDN variables/VDN override -> contact attributes or flow parameters; EAS skill levels -> proficiencies/routing criteria or routing profile priority and delay; ICM percent allocation -> DistributeByPercentage; Five9 call variables and Query modules -> attributes + Lambda; vector loops with wait-time -> queue flow loop with Loop block), and how to run the factory (generate, lint, golden path suites, human review, parallel run). Partial: two or three items. Zero: none. |
Total: 100
