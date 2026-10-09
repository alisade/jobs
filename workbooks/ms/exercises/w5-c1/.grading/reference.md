# Reference: ms/w5-c1 Dataverse access explainer

Reference code: `.grading/solution/src/dvaccess/access.py` and `model.py`.

## Shape of the solution

`explain()` walks three sources and appends a `Grant` for every match:

1. Direct role assignments: for each assignment of the user, read the role's depth for (table, privilege).
   Basic covers records the user owns; Local compares the record's `owning_bu` with the assignment BU; Deep
   uses `bu_in_subtree(record.owning_bu, assignment.bu)`; Global always matches.
2. Owner-team roles: for each owner team containing the user and each role assigned to that team, the same
   depth test but scoped to the team assignment's BU. Basic covers team-owned records, plus member-owned
   records when the role's inheritance is `direct`.
3. Shares: only if the user holds the privilege at Basic+ from any role path (`_max_depth`), add a grant for a
   share to the user and for a share to any team (owner or access) the user is in.

`can()` is `bool(explain())` so the two can never disagree. `can_associate()` is Append on child AND AppendTo
on parent.

## Why each rule

- Depth relative to the assignment BU is what makes modernized business units work: Priya sits in Finance but
  her Dispatcher role assigned from East reads East work orders only.
- The record's owning BU, not the owner's BU, decides Local/Deep: with record ownership across business units
  the two can differ.
- Shares are exceptions layered on roles. Learn defines User (Basic) access as "records they own, objects that
  are shared with them, and objects that are shared with a team that they're a member of", which is why a share
  is only usable with at least Basic depth for that privilege.
- Team privileges only vs Direct User (Basic) access level and Team privileges: the first lets members work with
  team-owned records only; the second also grants the Basic privileges directly.

## Ticket answers

- WO-1005 / Maria: `[share] record shared with user maria.dispatch (Read)`. By design: lena shared it; Maria
  has Dispatcher Basic+ read so the share is effective. Not a leak, but the share is an exception to audit.
  Maria cannot Write it.
- WO-1003 / Tomas: `[team-role] team west-dispatch-pool role Dispatch Pool (Basic)`. With the fixed library he
  CAN read it; if he still can't in the app, check he is really a member (group team sync) or the record owner.

## Alternatives and production notes

- Ground truth: the `RetrievePrincipalAccess` message (Web API function `RetrievePrincipalAccess`) or the
  Check Access button in a model-driven app returns the effective rights for a principal on a record.
- Not modelled: hierarchy security (manager / position), column-level security, access team templates,
  cascading assign/share on parent change, org-owned tables (only None/Global), business-unit default teams.
- Scale: precompute per-user (table, privilege) max depth and BU subtree sets; shares indexed by record.

## Interview angles

- "A user has Local read and is moved to a different BU. What changes for records they already own?"
- "Why is sharing a performance concern in Dataverse (PrincipalObjectAccess) and what would you use instead?"
