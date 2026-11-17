# Reference: connect/w2-c2

Reference simulator: `.grading/solution/src/sim.ts`; tuned design:
`.grading/solution/inputs/tuned-config.json`.

Baseline (seed 20261102, 30 s threshold): password reset 100% (tier 1 idle much of the time),
general ~89%, SAP apps ~53% with 20% abandon, VIP ~46% with 46% abandon. Causes:

- rp-apps lists q-general at priority 1 and q-apps at priority 2: the apps team spends the peak on
  general calls while SAP contacts wait out step 1 (SAP >= 4), which only the apps team meets.
- rp-vip has q-vip and q-general both at priority 1 with no delay: an older general call beats a
  newer VIP call, and VIP patience is short.
- Tier 1 is dedicated to password reset and idles while general overflows.

Tuned design (all queues >= 80%, VIP ~96%, apps ~95%): dedicated work first, shared work second
with a delay. rp-tier1: password reset p1, general p2 delay 10 s. rp-general: general p1, password
reset p2 delay 20 s, apps p2 (generalists meet step 2 and the fallback). rp-apps: apps p1, general
p2 delay 45 s. rp-vip: VIP p1, apps p2, general p3 delay 90 s.

Robustness: on seeds 1-3 general drops to 70-81% and password reset to 77-86% at the same staffing, so the
honest recommendation is the tuned design plus about two more general agents at the peak or a
callback offer on general; that is the kind of statement the steering committee needs.

Connect mapping: queue priority and delay live in the routing profile; contact priority and queue
time adjustment are set in the flow (Set routing behavior); proficiency steps come from Set routing
criteria using predefined attributes; after the last step expires the contact can go to any agent
on the queue.
