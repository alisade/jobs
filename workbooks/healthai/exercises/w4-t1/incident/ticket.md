# INC-48512: reviewer's decision appeared on a different member's determination

**Reported by:** RN reviewer rn-104 via the UM support desk, 2026-11-20 11:05 ET
**Severity:** critical (wrong determination letter for a member; potential privacy incident)

"At 10:42 I approved PA-2026-0003 (member M-100201). My approval never showed on that case: it is
still waiting for review. The letter queue has an approval signed by me for PA-2026-0008, a different
member I never opened. Dr. md-007 says their denial of PA-2026-0002 also ended up on PA-2026-0008."

The letters were held before mailing. Privacy is asking whether member data crossed between cases.

The app team's first theory: "cases for members with several open PAs share a thread, because the
thread id is derived from the member". Release 2026.11.3 (2026-11-19) included PA-2290 "reduce
allocations in the review service".

Attached: `audit-export.jsonl` (written by `make setup`, the 10:42 burst replayed against synthetic
cases). `make repro` replays it live.
