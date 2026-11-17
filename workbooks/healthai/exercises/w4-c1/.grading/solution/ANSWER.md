# ANSWER: healthai/w4-c1 PA intake graph with human review

## Approach

Rebuilt the prototype as validate -> fetch_coverage -> check_completeness -> (request_info | assess |
human_review) -> finalize. The only edge into finalize without a person is `auto_approvable`: a valid
recommendation, outcome approve, confidence >= threshold, every criterion met and cited, coverage active
and nothing missing. Anything else, including states nobody anticipated, falls through to human_review.
Eligibility problems skip the model entirely because they are potential denials.

## Fix

- assess validates with `Recommendation.model_validate_json`; invalid output becomes `model_error` and
  goes to review instead of crashing or approving.
- human_review interrupts with the recommendation and the reason for review; bad reviewer input loops
  back with `review_error`; deny/pend need a specific reason (CMS-0057-F).
- finalize re-checks the invariant and raises if asked to deny, pend or low-confidence approve without a
  human decision. Proven by the exhaustive test that drives every case with every reviewer answer, and
  by calling finalize directly on an unreviewed denial.
- Resume after restart proven with SqliteSaver on a file: the model is not called again.

## Trade-offs / what I would do in production

PostgresSaver, thread id `pa:<case_id>` (not member id). Checkpoints and interrupt payloads hold PHI:
keep the database in the BAA boundary, CMEK, retention tied to the case record, audit who reads it.
Tune the threshold on labelled cases and track the auto-approval rate and overturn rate per reviewer.
Trace every node and model call (OTel), and record the CMS-0057-F deadline on the case so the review
queue sorts by time remaining.
