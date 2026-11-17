# Decision request: ICD-10-CM code extraction for PA intake (Kestrel Health Plan, fictional)

The intake team wants diagnosis codes suggested from the free-text clinical notes attached to PA requests
(about 38,000 notes a month, peaks of 2,600 a day). Codes are suggestions for the nurse, never a decision.
Two options were tried on the same synthetic, held-out set of 300 notes (built from Synthea conditions plus
templated note text; no PHI):

- **A. Prompted large model** (Gemini on Agent Platform, 5 examples in the prompt, JSON output validated by Pydantic).
- **B. LoRA-tuned small open model** (a 2B-parameter open model, LoRA rank 16, alpha 32, dropout 0.05,
  target modules q/k/v/o projections, 2,000 training notes, 3 epochs), served on a dedicated Agent Platform
  endpoint with vLLM on one L4 GPU, min replicas 1.

You decide which to ship first, how to evaluate it continuously, and how to run it inside the HIPAA boundary.
