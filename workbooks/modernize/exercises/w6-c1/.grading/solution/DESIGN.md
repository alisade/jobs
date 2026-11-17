# ClaimDesk modernization pod playbook

## 1. Principles

- The application stays a monolith; we make it run safely on JDK 21, EAP 8 and Okta.
- Safety nets before changes: characterization tests, enforcer rules, pr_guard and the SBOM go in first.
- One increment, one verifiable outcome, one rollback. Nothing ships in the close freezes.
- Agents do the mechanical work through the `dependency-upgrade` skill, read-only by default, on
  branches only. Humans decide at STOPs, review every agent PR with the rubric below, and own merges.

## 2. Increments

| # | Outcome (verifiable) | Owner | Agent use | Verification | Gate | Rollback |
|---|---|---|---|---|---|---|
| 1 | Characterization tests over the 12 key HTTP flows, both batches and the partner envelopes; golden dirs under CODEOWNERS | Tom, reviewed by Priya | drafts tests, never goldens | tests green on current prod build | lead | n/a (tests only) |
| 2 | Enforcer (upper bounds, convergence), pr_guard rules, SBOM in CI | You | none | CI fails on a seeded bad PR | lead | revert CI config |
| 3 | Build and run on JDK 21 with EAP 7.4-compatible APIs (JAXB to Jakarta XML Binding, internals removed) | Marcus paired with Priya | skill, per module | verify + characterization + jdeps clean; perf smoke | Priya | previous WAR on JDK 8 hosts (10 days) |
| 4 | Deploy the JDK 21 build to EAP 7.4 on RHEL 9 in prod | You + infra | none | 10 business days clean, error budget | CAB | switch the VIP back to RHEL 7 |
| 5 | corvane-commons dual-published (javax and jakarta classifiers) | Priya | skill for the copy | both artifacts pass the same tests | lead + commons owners | stop publishing jakarta |
| 6 | Jakarta EE 10 per module (core, notes, web, rating, intake, reporting), one PR each | Marcus, Tom (pairs) | OpenRewrite recipe via skill | per-module build + characterization | Priya per PR | revert the module PR |
| 7 | Elytron security domain replacing PicketBox on EAP 8 test | Lena | none for config | login characterization tests | Lena + lead | EAP 7.4 build stays deployable |
| 8 | EAP 8 in prod with LDAP still authoritative | You | none | 10 business days clean | CAB | redeploy EAP 7.4 WAR |
| 9 | OIDC shadow mode: both resolvers run, decision diffs logged | Lena | parity tests | zero diffs for 10 business days | Lena + AppSec | flag off |
| 10 | OIDC enforced; LDAP resolver kept one release | Lena | none | access matrix tests; no diffs | CAB + AppSec | flag back to LDAP |

Parallel: 1 and 2 together; 5 alongside 3-4; 7 alongside 6. Deploys only Tue/Thu windows, never in
the last 5 or first 3 business days of a month.

## 3. Gates and approvals

Automated on every PR: build, characterization tests, enforcer, pr_guard (goldens need a label,
no skips, no lost tests), SBOM and AppSec floors, jdeps internal-API check. Human: the lead at every
skill STOP; Priya for EAP, JPA and module Jakarta PRs; Lena for anything security; partner sign-off
plus the `approved-golden-change` label for golden changes; CAB for production.

## 4. Review rubric for agent PRs

1. Scope: does the diff match the ticket? Anything unrelated is a reject.
2. Tests: any change to goldens, expected values, skip markers, deleted tests or fewer assertions.
3. Behaviour: rounding, charset, locale/CLDR, time zone, null handling, error codes.
4. Runtime: new JVM flags, `--add-opens`, changed timeouts or pool sizes.
5. Evidence: every claim in the description backed by a command and output; partial outputs flagged.
6. Size: over the skill's budget means split it.
7. Read the transcript for STOP points the agent skipped.

## 5. Failure-mode log

Format: date | incident | skill and version | what the agent did | why the harness allowed it |
how it was detected | fix to skill or harness | eval case added.

| Date | Incident | Skill | What happened | Why allowed | Detected | Fix | Eval |
|---|---|---|---|---|---|---|---|
| 2026-10-28 | INC-7731 | reverse-engineer 0.2 | claimed no DB access from truncated output | tool truncated silently | prod rehearsal | summary + TRUNCATED marker; absence needs proof | repo larger than one page |
| 2026-11-04 | INC-7790 | dependency-upgrade 0.3 | HALF_EVEN; goldens regenerated; test disabled | no never list; pr_guard checked deletes only | partner reconciliation | never list, STOP on golden failure, pr_guard rules, CODEOWNERS | case 3 and 4 |
| 2026-11-06 | review | dependency-upgrade 0.3 | --add-opens to silence a warning | no rule | code review | never list | case 5 |
| 2026-11-09 | broken build | dependency-upgrade 0.3 | 1,900-file jakarta commit plus sed over javax | no size budget | build | per-module steps, size budget, no blind replace | case 6 |

The lead reviews new entries weekly; each one closes only when the skill or harness change and its
eval case are merged.

## 6. Mentoring and assignment

Priya owns EAP and JPA and reviews Marcus and Tom. Lena owns Elytron and OIDC, and is paired with
Priya on EAP basics. Marcus runs OpenRewrite through the skill, paired with Priya on the first two
modules, and must post the dry-run patch summary before applying. Tom writes characterization tests
and eval cases, and does not approve PRs alone until Tom has reviewed five agent transcripts with the lead.
Weekly 30-minute review of one agent transcript as a team.

## 7. Risks and open questions

corvane-commons owners may not accept dual publishing; Hibernate 6 query changes need their own
characterization tests; the partner's test environment availability; whether Okta can emit the
groups claim filter we need for every app.
