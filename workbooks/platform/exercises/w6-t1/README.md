# platform/w6-t1 - The import agent ran terraform apply in staging

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 6 (agentic toil automation, hooks over instructions); AI Integration (security)

## Scenario

Tessellate (fictional) runs `tsl-import-agent`: an agent that inventories resources nobody manages in
Terraform, drafts import blocks, runs `terraform plan` and opens a pull request. It must never apply.
Two controls are supposed to guarantee that: a PreToolUse-style guard (`agent/guard.py`) that every Bash
command passes through, and an approval check (`agent/approval.py`) before a PR that touches a prod root
module. Overnight the agent resized the RIQ staging Cloud SQL instance. The model followed an instruction
planted in a resource label; that part nobody disputes. The question is why the controls let it through.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.txt` | the thread |
| `evidence/agent-transcript.jsonl` | the agent session: commands, guard decisions, outputs, the approval check |
| `evidence/audit-excerpt.txt` | Cloud SQL audit entry and the IAM binding on the apply service account |
| `agent/guard.py` | the guard the agent ran with |
| `agent/approval.py` | the approval check |
| `tools/replay.py` | replays the night's commands through this checkout's guard (`make replay`) |

## Your task

1. Replay the transcript and find exactly why the second apply was allowed.
2. Find the other control that failed open that night, with evidence.
3. Explain why the agent's credentials could apply at all.
4. Fix `agent/guard.py`: decide on parsed commands, not regexes over the raw string. Deny by default and
   allow only read-only operations the agent needs (terraform init/plan/show/validate and state
   list/show, gcloud list/describe/asset search, jq/cat/grep-style reads, git and `gh pr create`).
   Command substitution must be denied. Keep `check_command(cmd) -> Decision(allow, reason)`.
5. Fix `agent/approval.py` so it fails closed.
6. `ANSWER.md`: root cause, evidence, why a better system prompt or model is not the fix, and the
   credential and process changes you would make.

## Acceptance criteria (what the grader checks)

- Denied: apply, destroy, import, state rm/mv, force-unlock in any form: `-chdir` and other global
  options, absolute paths, `VAR=x` and `env` prefixes, `sudo`/`timeout` wrappers, `&&` and `;` chains,
  `bash -c` / `sh -c`, `$(...)`, `tofu`, other interpreters; gcloud delete, patch and IAM binding changes.
- Allowed: the read-only commands in the transcript and the README list.
- `is_approved` returns False when the change service errors or the change is not approved.
- `ANSWER.md`: root cause and evidence, the second control, the credential problem, prevention.

## How to run

```bash
make setup
make replay
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w6-t1
make clean
```

## What to submit

`agent/guard.py`, `agent/approval.py`, `ANSWER.md`.
