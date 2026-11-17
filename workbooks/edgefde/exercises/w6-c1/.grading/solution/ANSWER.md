# ANSWER: edgefde/w6-c1 Engagement brief, decision record and handoff plan

## Approach

Pulled every number out of the inputs first (failures, downtime, costs, sensors on hand), then
mapped each stakeholder to what they will judge the pilot on, then cut scope to what can be measured
in 8 weeks inside the change windows.

## Fix

Key decisions in BRIEF.md: (1) frame it as surprise bearing failures costing about USD 187k a year,
not as "AI"; (2) pilot on the 4 pumps that already have sensors, with a measured thin slice in two
weeks; (3) false alarms per machine-week as a signed hard cap, with shadow mode before going live;
(4) features and model on the gateway so raw data never leaves the site, model updates as a standard
change with canary and rollback; (5) Ravi's team owns the model, runbooks and eval suite at the end.

## Trade-offs / what I would do in production

Traded scope (ten pumps, seals, chatbot) and Dana's January date for a credible measured result.
First thing to validate with the client: that the 2023 trial data really contains the run-up to a
failure and lines up with the CMMS dates; without labels the recall metric needs renegotiating.
