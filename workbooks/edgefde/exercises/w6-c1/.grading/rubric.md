# Rubric: edgefde/w6-c1 Engagement brief, decision record and handoff plan
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0) |
| 2 | Framing and baseline | 20 | Full: problem = unplanned bearing failures on the transfer pumps; cost from inputs with arithmetic: 7 failures / 2 years = 3.5 per year x (6,200 + 9.5 h x 4,800 = 45,600 + 6,200 = 51,800) = about USD 181k per year, plus unnecessary planned swaps (about half of 10 pumps x 12/18 swaps per year x 1,900, about USD 6k); baseline detection is a monthly handheld route. Partial: cost stated without arithmetic. Zero: "deploy AI" framing. |
| 3 | Metrics | 15 | Recall on the labelled past failures (and the one run-up in the 2023 data), false alarms per machine-week with a hard cap (for example <= 0.1, so at most about one false alarm every two and a half weeks across four pilot pumps) because of Sam, lead time before failure (days), work orders raised through Joe's queue; measurement method and sign-off owner (Ravi, Sam). |
| 4 | Scope and constraints | 15 | Pilot on the 4 pumps that already have sensors; seals, motors, energy and the chatbot out of scope or later with reasons; raw waveforms stay on the gateway, only features and alerts leave via the proxy allow-list; no PLC or historian writes; change windows and a standard change for model updates with rollback; Python skills gap addressed. |
| 5 | Thin slice and plan | 15 | Week 1-2: one pump end to end (sensor, gateway features, alert into a test CMMS queue, dashboard) measured against the baseline, change request filed in week 1 for the second-Sunday window; a weekly path to 4 pumps, then the decision on all ten. |
| 6 | ADR | 10 | At least three options (raw to cloud, edge features + cloud model, all on gateway / on-prem level 3), decision honours residency and network, trade-offs (model updates, compute, operability), revisit triggers. |
| 7 | Stakeholders and handoff | 15 | Addresses Dana's January/all-pumps ask with a credible alternative for the VP review (4 pumps with measured numbers), Sam's false-alarm fear with a shadow mode period, Joe's queue, Ravi's ownership; handoff list (repo, model card, runbook for retrain / roll back / add a pump, eval suite, site readiness checklist, training session) each with a client owner. |
| 8 | Clarity | 10 | Readable in 10 minutes, numbers sourced, a diagram, ANSWER.md summarises decisions. |
Total: 100
