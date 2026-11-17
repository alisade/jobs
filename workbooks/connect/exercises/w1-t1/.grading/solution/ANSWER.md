# ANSWER: connect/w1-t1 "All specialists are busy" on repeat

## Approach

Read PAGE.txt, then counted CTRs by DisconnectReason and Queue per 15 minutes, then followed one looping
ContactId through the flow logs, then diffed the two exported flows.

## Root cause

`check-staffing` has Parameters.QueueId pinned to q-password-reset (present since 2026.09.30). CHG-48211
routed set-q-overflow back to check-staffing. When PasswordReset went to 0 staffed at 14:00 (realtime CSV),
every caller cycled check-staffing(False) -> overflow-msg -> set-q-overflow -> check-staffing:

    jq -r 'select(.Identifier=="check-staffing")|[.Results,.Parameters.QueueId]|@tsv' incident/flow-logs/*.log | sort | uniq -c
      207 False  arn:...:queue/q-password-reset
       24 True   arn:...:queue/q-password-reset

CTRs: 28 CUSTOMER_DISCONNECT with no queue, all after 14:00. ContactFlowErrors 0: a loop is not an error.
Okta: 429 retries succeeded, Lambda Errors 0, option 2 callers loop without invoking the reset Lambda.

## Fix

Removed the pinned QueueId (check the working queue), and the overflow path now re-checks GeneralSupport in
its own block; nobody staffed -> message, disconnect. make lint clean, make simulate for each option with
PR_STAFFED=0, make test passes.

## Trade-offs / what I would do in production

CI: graph lint + staffing-matrix simulation + Connect test cases; alarm on short no-queue contacts from the
CTR stream; review rule against hard-coded QueueIds in shared blocks or modules. A callback offer would be
better than disconnecting when nobody is staffed.
