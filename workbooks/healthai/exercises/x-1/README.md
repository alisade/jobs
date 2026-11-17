# healthai/x-1 - Design: LoRA-tuned small model vs prompting for ICD-10-CM extraction

**Type:** design (rubric-graded, no automated tests) | **Estimate:** 2 hours | **Study plan:** Week 7 add-on (PEFT/LoRA)

## Scenario

Kestrel Health Plan (fictional) wants ICD-10-CM codes suggested from clinical notes attached to PA
requests. Two options were measured on the same synthetic held-out set: a prompted large model and a
LoRA-tuned 2B open model on a dedicated Agent Platform endpoint. The VP asks for a one-page decision with
numbers, and an evaluation and compliance plan. Read everything in `inputs/`.

## Your task

Write `DESIGN.md` (fill every section of the template) and `ANSWER.md`:

1. Recommend what ships first and why, using the measured numbers.
2. Compute cost per 1,000 notes and per month for both options at 38,000 notes a month, including the
   always-on endpoint, and the break-even volume.
3. Analyse quality by slice: where LoRA wins, where it loses, and what that means for nurses.
4. Architecture on Agent Platform (endpoint type, VPC-SC, CMEK, audit logs, how the PA graph calls it),
   with a diagram.
5. Evaluation and release gates, shadow mode, drift monitoring.
6. How each option handles the October 1 code-set update.
7. PHI and compliance: training data provenance, de-identification, BAA scope.

## Acceptance criteria (rubric)

Correct arithmetic, a decision that follows from the numbers and the constraints, a real treatment of
rare codes and invalid codes, a deployable architecture inside the HIPAA boundary, and gates that would
catch a regression.

## Run

```
make setup     # nothing to install
make test      # completeness report
# then from workbooks/ in Claude Code: /grade healthai/x-1
```
