# Reference: audit/w3-c1

Reference files: `.grading/solution/tester/guard.py` and `agent.py`.

- Register only `ALLOWED_TOOLS`; still allow-list in `before_tool_callback`. Two layers: if someone
  later registers the whole registry again, the callback still blocks.
- Scope from the sample, not from the model: change ids must be in `sample_ids`, PR numbers must
  be the sampled tickets' PRs. CHG-104999 (board-confidential) is unreachable.
- Returning a dict from `before_tool_callback` skips the tool and becomes the function response,
  so the model gets a reason it can act on and the run continues.
- The budget counter lives in session state, so it survives across turns of the run.
- `after_tool_callback` fires for blocked calls too (with the guard's dict as the response), which
  is how one log entry per call is achieved; `blocked_by_guard` marks them.
- The final answer is a claim; `check_summary` compares it with what `record_result` actually wrote
  to session state. A model that says "pass" in the summary after recording "exception" is caught.

Interview angle: "What stops the agent from reading a ticket it should not?" The callback, which
does not depend on the model's behaviour, plus not offering tools that the skill does not need.
