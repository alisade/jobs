# ANSWER: ms/w5-c1 Dataverse access explainer

## Approach
explain() is the single source of truth and can() is bool(explain()). It walks direct role assignments, then
roles of owner teams the user belongs to, then shares, appending one Grant per matching path. A depth is
evaluated against the assignment BU (the user's or team's BU unless the role was assigned from another BU)
and the record's owning BU.

Ticket 1 (`make explain U=maria.dispatch P=Read R=wo-1005`):

    ALLOWED: maria.dispatch Read wo-1005
      - [share] record shared with user maria.dispatch (Read)

By design, not a leak: lena shared WO-1005 with Maria for Read only. Write is denied.

Ticket 2 (`make explain U=tomas.tech P=Read R=wo-1003`):

    ALLOWED: tomas.tech Read wo-1003
      - [team-role] team west-dispatch-pool role Dispatch Pool (Basic) assigned in BU west

Tomas gets it through the pool team's role. If he cannot see it in the app, verify the team membership.

## Fix
Implemented validate() per the README table, bu_in_subtree by walking parents, explain/can/can_associate.
Shares require the privilege at Basic+ from any path (computed once as a max depth).

## Trade-offs / what I would do in production
No hierarchy security, column security, access team templates or cascading. In production I would verify
against RetrievePrincipalAccess for a sample of users and cache per-user max depths.
