# ANSWER: connect/w2-t1 Password-reset service level collapsed after a routing change

## Approach

Compared the PasswordReset metrics before and after Sunday, then the queue-time distribution in the
contact records, then the profile exports and the real-time snapshot. Checked the training day last.

## Root cause

rp-service-desk has PasswordReset at priority 1 but Delay 20, copied from rp-general where it was a
20 s overflow. Profile delay means agents only get a contact after it waited 20 s. Evidence:
`jq ... .Queue.Duration` for answered PasswordReset contacts: minimum 20 s every day after 10-05,
majority under 10 s the week before; snapshot 08:56: 4 waiting (oldest 13 s) with 4 desk agents
Available. Metrics: SL 86% -> 70%, ASA 8 s -> 25 s, abandons 6% -> 18%. Smoke test passed because one
call answered after 20 s still counts as answered.

## Fix

Delay 0 on PasswordReset in rp-service-desk. make replay: PasswordReset 84.4% / 5.2% abandon / 8.1 s
ASA; General 84.4%; Applications 92.6%. Training day 60% -> 74%: staffing was not the cause.

## Trade-offs / what I would do in production

Review routing changes as a queue x priority x delay table with intent; replay demand before CAB;
pilot with a few agents; alarm on SL and on Available agents while contacts queue; do the PIR.
