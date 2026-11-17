# ANSWER: connect/w3-c3 Hybrid coexistence and porting cutover plan

## Approach

Grouped the inventory into port tickets by carrier and country, laid them against the wave
and freeze calendar, then checked each coexistence mechanism against the Connect and Chime SDK
docs (porting, external voice analytics, BYOC limits, PSTN audio migration).

## Fix

1. Forward first, port later: Avaya stays primary on 1-800 through Wave 2 and forwards a
   growing share to Connect-claimed numbers; port T1 on 2027-02-09.
2. No Voice Connector bridge into Connect: cross-platform calls go over the PSTN; context via a
   DNIS-pool handoff API with a TTL.
3. SIPREC from the Avaya SBCE to a conversational analytics connector covers recordings and
   analytics on Avaya calls from Wave 1.
4. UK port opened now (2-6 months); US/CA requests inside the 30-day window; no ports in freezes.
5. Rollback after a port is forward-back to Avaya DIDs kept live to T+30, because un-porting
   needs a new LOA.

## Trade-offs / what I would do in production

Rejected: porting everything in one event (single LOA failure stalls all waves) and asking for
a Voice Connector-into-Connect bridge (unsupported without AWS review, adds hops, loses
analytics). First validations: quotas with AWS, Lumen RespOrg change lead time, security's
acceptance of SIPREC analytics for the audit finding.
