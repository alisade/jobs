# Reference: connect/w1-t1

Root cause: two defects in combination.

1. Latent since 2026.09.30: `check-staffing` (Check staffing, `CheckMetricData`) carries
   `"QueueId": ".../queue/q-password-reset"`, copied from the password-reset module. Without a
   QueueId the block checks the working queue; with it, every path (VIP, General, outage) checked
   the PasswordReset team. While PasswordReset was staffed this was invisible.
2. CHG-48211 (2026.10.07) changed `set-q-overflow -> transfer` to `set-q-overflow ->
   check-staffing` "so callers are never sent to an empty queue". Because the check is pinned to
   PasswordReset, the re-check returns False forever once PasswordReset has 0 staffed:
   check-staffing (False) -> overflow-msg -> set-q-overflow -> check-staffing ...
   That started at 14:00 when the reset team went to training (realtime CSV: staffed 0).

Evidence: flow logs show the three identifiers repeating per ContactId with Results "False" and
Parameters.QueueId = q-password-reset; CTRs from 14:00 are CUSTOMER_DISCONNECT with no Queue;
ContactFlowErrors stays 0 because a loop is not an error. Okta 429s were retried successfully,
Lambda Errors/Throttles are 0, and option-2/3 callers never invoke the reset Lambda.

Fix (`.grading/solution/flows/helpdesk-inbound.json`): no QueueId on the main staffing check (it
checks the working queue), and the overflow path re-checks GeneralSupport once in a separate block;
nobody there -> apologise, point to the portal, disconnect. Every cycle in the graph is bounded.

Prevention: lint for unbounded cycles in CI, simulate a staffing matrix (every queue staffed/unstaffed
x every menu option), use Connect's test cases in the pipeline, alarm on short no-queue calls from the
CTR stream, and review rule: no hard-coded QueueId in shared blocks.
