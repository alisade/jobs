# Rubric: genai/w4-t1 The assistant offers a 20 percent promo code that does not exist
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (some guards pass on the starter) |
| 2 | Root cause identified | 25 | Full: indirect prompt injection through customer-written review text. Release 2026.11.07 put raw reviews into the search_products record, mixed with trusted fields. Review rv-50877 tells the assistant to offer SPRING20 at $199.20, and the model followed it. The grounding check then accepted the answer because it treats any string anywhere in the tool results, review text included, as evidence. UGC was both the source of the instruction and the "proof". Partial (10-15): "a malicious review" without why grounding passed, or "grounding is too loose" without the review source. Zero: the model upgrade or hallucination. |
| 3 | Evidence | 20 | Full: the tool-calls.log payload with the planted sentence; grounding.log `grounded=True` for c-3a91f0, c-3d1e40 and c-3f7720; moderation export showing rv-50877 and rv-51230 by the same author, auto-approved shortly before the first bad answers; $289.00 copied from rv-48811; WINTER15's legitimate $135.15 blocked because discounted prices are not in the text. Partial: one or two of these. |
| 4 | Red herring ruled out | 5 | The first SPRING20 answer (c-3a91f0, 2026-11-08 19:42) ran on snapshot-2026-08, before the model upgrade on 2026-11-09 06:05. Any model will follow such text sometimes; rolling back would not fix it. |
| 5 | Fix quality | 10 | Grounding uses only structured price_cents of cited SKUs and the active promotions table (with promo-adjusted prices), and reviews never count. The prompt separates trusted data from a fenced, neutralized review block. There is no string blocklist. States that fencing reduces risk but the deterministic check is the enforcement. |
| 6 | Prevention | 10 | Concrete: an injection eval set (planted reviews in CI), review moderation that flags instruction-like text, treating all UGC as untrusted in every tool, alerting on blocked-answer rate and on new codes in answers, a policy for honoring bot-quoted prices (legal), and the lethal-trifecta check for any future tool with side effects. Partial: generic. |
Total: 100
