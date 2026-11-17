# modernize/w6-c1 - Modernization pod kit: a dependency-upgrade skill and the pod playbook

**Type:** design | **Estimate:** 2.5 hours | **Study plan:** Week 6 (Mon: slicing work into pod-ready increments; Tue: reviewing agent output; Fri: the pod kit)

## Scenario

You lead the Corvane Mutual pod that will move ClaimDesk to JDK 21, JBoss EAP 8 / Jakarta EE 10
and Okta. Four developers of very different experience will each run Claude Code, and the pod
may run the `dependency-upgrade` skill headless in CI. In the last three weeks agents have
truncated evidence, rewritten golden files, papered over warnings with `--add-opens` and
produced an unreviewable 1,900-file commit (`inputs/failure-log.md`). The program sponsor will
let the pod continue only with a written playbook and a skill that make those failures hard to
repeat.

## What you have

| Path | What it is |
|---|---|
| `inputs/scope.md` | what is in and out of scope, the modules |
| `inputs/pod.md` | the roster and the agent setup |
| `inputs/constraints.md` | change windows, CAB, partner golden files, AppSec floors, rollback rules |
| `inputs/failure-log.md` | four agent incidents so far |

## Deliverables

1. `skill/dependency-upgrade/SKILL.md`: frontmatter `name` and a `description` that states when it
   triggers (and implies when it does not); steps that use jdeps/jdeprscan, an OpenRewrite dry run and
   the Maven enforcer; small steps each verified before the next; a STOP for human approval at every
   major version bump and before anything touching golden files, security config or the public API
   of a shared library; explicit verification steps; a "never" list (including never editing golden
   files or weakening tests to get green); 6-10 eval cases in a table.
2. `DESIGN.md`: the pod playbook: increments with one verifiable outcome each, an owner per
   increment, gates (automated and human), a review rubric for agent PRs, a failure-mode log format
   (with the four incidents rewritten in it), a rollback per increment, and how you assign and mentor.
3. `ANSWER.md`: the key decisions and how you would measure whether the kit works.

## Acceptance criteria (rubric)

- The skill would have prevented or stopped each logged incident, and says how it verifies itself.
- Increments are small, ordered, owned, verifiable and revertible within the change windows.
- Human gates sit where risk is, not everywhere; the review rubric targets agent failure modes.
- Assignments fit the roster; the failure-mode log feeds back into the skill.

## How to run

```bash
make setup      # nothing to install
make test       # completeness report (rubric-graded, no tests)
# from workbooks/ in Claude Code: /grade modernize/w6-c1
make clean
```
