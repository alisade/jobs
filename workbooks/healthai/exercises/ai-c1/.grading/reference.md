# Reference: healthai/ai-c1

See `.grading/solution/evals/gates.py`. Debrief points:
- Safety is a hard gate: one auto-finalized denial in 90 rows fails the build. An average would hide it.
- Wilson lower bound instead of the mean: with 180 criteria and 177 correct the bound is 0.952, so the
  0.88 threshold passes with margin; a 0.65 accuracy regression cannot slip through on lucky variance.
- Consistency is measured on the route (auto vs review), the decision that matters operationally; outcome
  wording between deny and pend may vary when a human reviews anyway.
- Substring citation support is a cheap deterministic first layer. A real system adds an LLM judge for
  "does this text support this criterion", calibrated on human labels, run after the cheap checks.
- Baseline updates are change-controlled: a PR that edits baseline.json needs a reviewer from the
  clinical/compliance side.
