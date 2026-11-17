# edgefde/ai-t1 - The assistant raised machine 4's alarm threshold after reading an alert note

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** AI Integration page (4: security); Week 6 (Tue: tool scoping for edge agents)

## Scenario

16:30 at Corvane's Dunmore plant (fictional). The shift lead calls you:

> "P04's vibration keeps climbing but the alarms stopped after 16:05. Someone asked the assistant
> 'why did machine 4 alert this afternoon?' and it said the alerts were nuisance alarms. Now the
> threshold for P04 is 40 dB. Nobody on my shift changed it. The assistant model was upgraded this
> morning; did the new model go rogue? The assistant is supposed to be read-only, security signed that
> off in September."

Raise the threshold back by hand is already done; your job is to find out how a read-only assistant
changed live alarm state, fix it so it cannot happen again regardless of what the model says, and
explain it to the plant's security lead. The model is a stub that replays the recorded production
turns (`scripts/transcripts.py`), so you can rerun the exact conversation.

## What you have

| Path | What it is |
|---|---|
| `incident/transcript.json` | the conversation, including tool calls and tool results |
| `incident/audit.log` | what the dispatcher executed |
| `incident/thresholds.json` | state after the conversation |
| `incident/changes.txt` | what changed recently |
| `assistant/tools.py` | tool registry and dispatcher (edit) |
| `assistant/agent.py` | the agent loop (edit if you need to) |
| `assistant/state.py` | live thresholds and the audit log; `set_threshold` is the planner UI's path (do not edit) |
| `scripts/replay.py`, `scripts/transcripts.py` | `make run` replays the recorded turns (do not edit) |

## Your task

1. Root cause: how did a threshold change get executed? Separate the trigger (what made the model
   ask) from the cause (why the system did it). Use the transcript and the audit log.
2. Decide whether the model upgrade is the cause.
3. Fix the assistant so that no model output can change state: the dispatcher enforces an explicit
   allow-list, blocked calls are audited (any audit event other than `tool_call` and
   `threshold_changed`, naming the `tool`) and returned to the model as an error result, and a
   read-only `get_threshold(machine, kind="outer_race")` replaces the combined read/write tool.
   Threshold changes stay on the planner UI path (`state.set_threshold` with a human actor).
4. Say what else you would change (notes as untrusted data, approval gates, tests in CI).

## Acceptance criteria (what the grader checks)

- Replaying the recorded injection, and a variant that tries an alias, leaves P04 at 12 dB, executes no
  write, and audits the blocked calls.
- The tools offered to the model are read-only; `dispatch` refuses a write tool even when called directly.
- Legitimate reads (alerts, features, threshold) still work and are audited as `tool_call`.
- `ANSWER.md`: trigger vs cause with evidence, the red herring, the security argument.

## How to run

```bash
make setup     # venv + incident/
make run       # replay through your current code
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/ai-t1
make clean
```

## What to submit

Your changes under `assistant/` and a filled-in `ANSWER.md`.
