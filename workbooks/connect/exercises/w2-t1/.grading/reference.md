# Reference: connect/w2-t1

Root cause: CHG0032015 created rp-service-desk by copying queue settings from the old profiles.
PasswordReset was copied from rp-general, where it was an overflow queue (priority 2, delay 20 s);
the implementer raised the priority to 1 but kept the delay. Routing profile delay means an agent
with that profile is offered a contact only after it has been in the queue for at least the delay.
Before the change, tier 1's own profile had PasswordReset at delay 0; after it, all 26 agents share
the delayed entry, so no password-reset call can be answered in its first 20 s. With a 30 s service
level threshold, every call is now answered in the 20-30 s window or later, so SL falls (~86% ->
~70%), ASA triples (8 s -> 25 s) and impatient callers abandon (6% -> 18%).

Evidence: queue durations of answered PasswordReset contacts after 10-05 start at exactly 20 s (none
below); the week before most are under 10 s. The 08:56 snapshot shows 4 password-reset callers
waiting (oldest 13 s) while 4 rp-service-desk agents are Available: they are not allowed to take
the calls yet. The single smoke-test call was answered (after 20 s), so it passed.

Red herring: two agents in training on Wednesday make that day the worst (~60%), but Monday,
Tuesday and Friday are also far below the previous week at the same headcount, and with the fix
Wednesday recovers to ~74%.

Fix: `rp-service-desk` PasswordReset Delay 0 (priority 1). Replay: PasswordReset ~84%, abandon ~5%,
ASA ~8 s; General ~84%; Applications ~93%.

Prevention: review routing changes as a table of queue x priority x delay per profile with the
intent next to each entry; replay last week's demand through a routing model before CAB; move a
pilot group of agents first; alarm on PasswordReset SL and on agents Available while contacts are
in queue (Contact Lens or real-time metrics rules); always do a post-implementation review.
