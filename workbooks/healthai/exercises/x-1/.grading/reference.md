# Reference: healthai/x-1

The numbers favour prompting at this volume: about $183/month vs about $620/month for an always-on L4
endpoint, break-even near 129k notes/month. LoRA wins micro F1 (0.884 vs 0.861) and latency (p95 690 ms
vs 4.2 s) because most notes carry common codes, but it loses badly on rare codes (0.488 vs 0.701) and
macro F1, and it has 3x the invalid-code rate and 9x the parse failures. In PA intake a missed rare
diagnosis can route a case to the wrong policy, so the slice that matters most is the one LoRA loses.
Latency is not a constraint for intake suggestions (a nurse reviews later).

A strong answer ships A now, validates every code against the official ICD-10-CM file, measures by slice in
CI, and keeps B as a funded experiment: more rare-code examples, constrained decoding to valid codes, and a
hybrid router (B for top-50 codes with high confidence, A otherwise) once volume or latency justifies the
endpoint. October 1: A needs a prompt/example refresh and code-file update; B needs a retrain (about $38
and 6 engineer hours) and a full re-eval before the deadline.
