# Engagement brief: Corvane Dunmore pump health pilot

Prepared by Tessellate Edge for Dana Whitcombe, Ravi Okafor, Sam Ferreira, Marta Lindqvist and Joe
Pressley. Version 1, 2026-11-06. Numbers come from the kickoff notes unless marked otherwise.

## Problem statement and who has it

The Dunmore transfer pumps fail their bearings without warning about 3.5 times a year. Each surprise
failure stops a line for most of a shift and costs about USD 52k. Reliability (Ravi) owns the
problem; maintenance planning (Joe) and operations (Dana) carry the cost. Time-based replacement at
18 months does not help: half the bearings pulled are fine and half fail earlier. The pilot's goal is
early warning of bearing degradation, days ahead, on the pumps that matter, without alarms the
operators learn to ignore.

## Current cost and baseline

| Item | Arithmetic | Per year |
|---|---|---|
| Unplanned failures | 7 in 24 months = 3.5 per year | |
| Cost per unplanned failure | 6,200 parts/overtime + 9.5 h x 4,800 lost production = 6,200 + 45,600 | 51,800 |
| Unplanned total | 3.5 x 51,800 | about 181,000 |
| Planned swaps not needed | 10 pumps x (12/18) swaps per year x 50% fine x 1,900 | about 6,300 |
| Total addressable | | about 187,000 |

Baseline detection: none in between monthly handheld routes (overall velocity only). None of the 7
failures were caught by the route.

## Target metrics and how they are measured

| Metric | Target | How measured | Signs off |
|---|---|---|---|
| Detection on known failures | catch the 2023 run-up and >= 5 of 7 labelled failures in replay | replay of the 2023 trial data and historian-aligned labels from the CMMS | Ravi |
| False alarms | <= 0.1 per machine-week in shadow mode, hard cap | every alert reviewed by Ravi's team during 4 weeks of shadow mode | Sam |
| Lead time | median >= 7 days before failure on replayed failures | alert timestamp vs CMMS failure date | Ravi |
| Work-order path | 100% of alerts land in Joe's planning queue, none go to techs directly | CMMS audit | Joe |
| Bandwidth and residency | 0 bytes of raw waveform leave the site | proxy logs reviewed with Marta | Marta |

These are agreed before week 1 ends; results are reported against them, not against impressions.

## Scope and out of scope

In scope: bearing health on the 4 pumps that still have the 2023 accelerometers; edge features and
alerts; alerts as draft work orders in Joe's queue; a simple dashboard; the handoff pack.

Out of scope for the pilot, with reasons:

- The other 6 pumps: sensors cost USD 2,400 plus installation and change windows; added after the
  pilot proves the metrics (decision gate in week 8).
- Seals, motor faults and energy: different sensors and failure physics; listed under "next".
- An operator chatbot: adds risk before the alerts are trusted; a read-only assistant is a later phase.

## Constraints

| Constraint | How the design honours it |
|---|---|
| No internet from level 2, proxy with TLS inspection | gateway talks only to level 3; level 3 sends features/alerts out through the proxy allow-list; CA bundle configured, verification never disabled |
| Raw data stays on site | waveforms processed and kept on the gateway (rolling 14 days); only features and alerts leave |
| Change control | change request filed in week 1 for the second-Sunday window; model updates as a documented standard change with automatic rollback |
| No PLC or historian writes | read-only OPC UA for motor current and flow; nothing writes to control systems |
| Site accounts | service account owned by Ravi; no shared logins |
| Skills | Python packaged as a service with a runbook; the reliability analyst trained to retrain from a notebook-free CLI |

## Thin-slice plan (weeks 1-2) and the 8-week path

Week 1-2 (thin slice): reconnect one pump's sensor to a gateway, compute features every minute,
write alerts as draft work orders into a CMMS test queue, show one dashboard, replay the 2023 data
through the same code and report recall and false alarms against the agreed metrics.

| Week | Outcome |
|---|---|
| 3-4 | all 4 pumps live in shadow mode (alerts reviewed, not acted on) |
| 5 | model v1 trained on labelled data, eval gate in CI, first model update through the standard change |
| 6 | shadow results reviewed with Sam and Ravi; threshold set from the false-alarm budget |
| 7 | alerts go live into Joe's queue; runbooks rehearsed by Ravi's team |
| 8 | results against metrics, handoff session, decision on the remaining 6 pumps |

## Architecture decision record

Context: raw data cannot leave the site, level 2 has no internet, model updates are changes.

| Option | For | Against |
|---|---|---|
| A. Raw waveforms to a cloud analytics service | easiest modelling | violates residency; bandwidth; dead on arrival |
| B. Features on the gateway, model and alerting in the cloud | central updates | alerts depend on the WAN; feature upload still needs approval |
| C. Features and model on the gateway, summaries out | works offline, residency by design | model updates need a fleet process; small compute |

Decision: C, with a level 3 service for the dashboard and CMMS integration, and features/alerts sent
out only for Tessellate Edge support and retraining. Model updates through a canary on one pump with
automatic rollback. Revisit if the plant approves a private cloud region or if models outgrow the
gateway.

```text
[accelerometer] -> [gateway L2: features, ONNX model, buffer] -> [L3 service: dashboard, CMMS draft WO]
                                                              -> [proxy L3.5 allow-list] -> features/alerts only
```

## Risks

| Risk | L / I | Mitigation |
|---|---|---|
| False alarms erode trust (2023 repeat) | M / H | shadow mode, hard false-alarm budget, Sam signs the threshold |
| Too few labelled failures | H / M | replay 2023 run-up, physics-based features first, anomaly model before classifier |
| Missed change window slips 4 weeks | M / M | file in week 1, standard change for model updates |
| Gateway or sensor hardware faults | L / M | health telemetry, spare gateway on site |
| VP timeline pressure to scale early | M / H | measured 4-pump result is the VP story |

## Stakeholders and how you will handle the conflicting asks

- Dana: the 2026-02-12 VP review gets a measured result on 4 pumps (recall on past failures, false
  alarm rate, cost avoided per failure caught) and a costed plan for all ten; that is a stronger
  story than ten pumps with unknown accuracy.
- Sam: shadow mode first, false alarms are a signed metric, nothing writes to the PLCs.
- Marta: architecture C keeps raw data on site; standard change with rollback for model updates.
- Joe: alerts are draft work orders in the planning queue only.
- Ravi: owns the model, the runbook and the retrain process at the end.

## Handoff assets (customer-owned)

| Asset | Client owner |
|---|---|
| Code repository in Corvane's Git with CI | Ravi (plant IT hosts) |
| Model card and eval suite they can rerun | Ravi |
| Runbooks: retrain, roll back a model, add a pump | Ravi's analyst |
| Site readiness checklist (proxy, CA bundle, offline install kit) | Marta |
| Alert-to-work-order procedure | Joe |
| Dashboard and threshold rationale | Sam |
| Handoff session recording and Q&A | Dana |

## What we would do next

Instrument the other 6 pumps if the metrics are met, add motor current signature analysis from the
historian, then a read-only operator assistant over alerts and the model card.
