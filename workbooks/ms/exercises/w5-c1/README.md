# ms/w5-c1: Dataverse access explainer for Tailspin Field Services

Type: coding. Estimate: 2-3 h. Exam: AB-400 - Build solutions (15-20%); the Dataverse security model is assumed knowledge across every AB-400 domain (application users, plug-in identity, sharing in code).

## Scenario

Tailspin Field Services runs dispatch on a Dataverse environment (`tsfs-prod`). The service desk gets the
same two tickets every week:

- "Why can Maria, a West dispatcher, open work order WO-1005 from the East region? That's a data leak."
- "Tomas can't see the pool work order WO-1003 even though he's in the West dispatch pool team."

Nobody can answer quickly, because access in Dataverse is the union of direct roles, team roles, business-unit
depth, modern (cross-BU) role assignments and record shares. The platform team wants a small Python library
that loads an export of the security model and answers `can(user, privilege, record)` plus `explain(...)`:
every path that grants the access, so a support engineer can paste it into the ticket.

The export format is `data/tailspin.json` (business units, users, teams, roles, assignments, records, shares).

## The security model you must implement

These rules follow the Learn pages linked below. Where Dataverse has subtleties that this export does not
carry, the rule below is the contract the tests use.

1. **Privileges** per table: `Create, Read, Write, Delete, Append, AppendTo, Assign, Share`.
2. **Depths** (access levels): `None < Basic < Local < Deep < Global`. The loader also accepts the role editor
   names `User`, `Business Unit`, `Parent: Child Business Units`, `Organization` (already done for you).
   - Basic (User): records the principal owns.
   - Local (Business Unit): records whose **owning business unit** equals the scope BU.
   - Deep (Parent: Child Business Units): records whose owning BU is the scope BU or any descendant.
   - Global (Organization): every record of the table.
3. **Roles are cumulative**: any granting path is enough; a narrower role never hides a record.
4. **Scope BU of a role assignment** is the BU the role was assigned from. Default is the principal's own BU.
   With modernized business units (record ownership across BUs) a role can be assigned from another BU
   (`"bu": "east"` on the assignment), and its depth is evaluated relative to that BU, not the user's BU.
5. **Record owning BU** defaults to the owner's BU but may be set explicitly (`owning_bu`). Local/Deep checks use
   the record's owning BU, never the owner's BU.
6. **Owner teams** can own records and hold roles; a member gets the team's roles. Depths of a team role are
   evaluated relative to the team assignment's BU (the team's BU by default).
   - Basic depth on a team role covers records **owned by the team**.
   - Role `inheritance` models the "Member's privilege inheritance" setting:
     `"direct"` (Direct User (Basic) access level and Team privileges, the default for new roles) means Basic
     also covers records the member owns personally; `"team_only"` (Team privileges only) means it does not.
   - A user's own Basic privilege does not cover records owned by a team they belong to.
7. **Access teams** have no roles and own no records; they only receive shares.
8. **Sharing** grants specific rights on one record to a user or a team (members inherit it). `Create` cannot be
   shared. A shared right is only effective if the user holds that same privilege on the table at Basic depth
   or better from any of their roles (direct or via an owner team).
9. **Associate** (attach a note to a work order): `Append` on the child record and `AppendTo` on the parent.

### Validation rules (`SecurityModel.validate()`)

| Rule | Error |
|---|---|
| Exactly one root BU (parent `null`) | `ValueError` |
| Every BU parent exists; no cycles in the hierarchy | `UnknownEntityError` / `ValueError` |
| Users and teams reference existing BUs; team members are existing users; team type is `owner` or `access` | `UnknownEntityError` / `ValueError` |
| Role inheritance is `direct` or `team_only`; role privileges are known names | `ValueError` |
| Assignments reference an existing role, BU and principal | `UnknownEntityError` |
| Access teams cannot be assigned roles or own records | `ValueError` |
| Records have an existing owner and owning BU | `UnknownEntityError` |
| Shares reference an existing record and principal and only shareable rights | `UnknownEntityError` / `ValueError` |

## Your task

Fill in the TODOs:

- `src/dvaccess/model.py`: `SecurityModel.validate()` (parsing is already done).
- `src/dvaccess/access.py`: `bu_in_subtree`, `explain`, `can`, `can_associate`.

`explain()` returns a list of `Grant(kind, role, team, depth, scope_bu, detail)`:
`kind` is `role`, `team-role`, `share` or `team-share`; one entry per granting path (a role assignment that
matches, a team role that matches, a share to the user, a share to a team the user is in). Empty list = denied.
Unknown user or record raises `UnknownEntityError`; an unknown privilege raises `ValueError`.

Then answer the two tickets with the CLI and put the output in `ANSWER.md`:

```
make explain U=maria.dispatch P=Read R=wo-1005
make explain U=tomas.tech P=Read R=wo-1003
```

## Acceptance criteria

- All four depths behave as above, including Local not reaching child BUs and Deep never reaching the parent.
- Modern BU assignments evaluate depth relative to the assigned BU.
- Team-owned records, both inheritance modes, and team roles scoped to the team's BU.
- Shares (user and team, including access teams) grant only the shared rights and only with a Basic+ privilege.
- `can_associate` requires Append on the child and AppendTo on the parent.
- `explain` lists every granting path with role/team/depth/scope BU filled in.
- `validate()` enforces the table above.

## How to run

```
make setup     # uv sync
make test      # visible tests (the hidden ones cover edge cases and validation)
make explain U=<user> P=<privilege> R=<record>
make clean
```

## What to submit

Your code in `src/dvaccess/` and `ANSWER.md` (Approach, Fix, Trade-offs). In the Approach, answer both
service-desk tickets with the `explain` output and say whether the WO-1005 access is a leak or by design.
Then run `/grade ms/w5-c1` from the workbooks folder.

## Study guide links

- [Week 5 Thu - Security model and governance](../../../../microsoft-adf-powerapps-study-plan.html#week5)
- [Security roles and privileges (access levels, member's privilege inheritance)](https://learn.microsoft.com/en-us/power-platform/admin/security-roles-privileges)
- [Ownership-based security, business units, matrix access, teams, sharing](https://learn.microsoft.com/en-us/power-platform/admin/wp-security-cds)
- [Manage teams](https://learn.microsoft.com/en-us/power-platform/admin/manage-teams)
- [Security concepts in Dataverse (developer)](https://learn.microsoft.com/en-us/power-platform/admin/wp-security)
