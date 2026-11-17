# Reference: edgefde/ai-c1

Reference files: `.grading/solution/assistant/{schema,tools,agent,router}.py`.

- `schema.py`: Pydantic constraints (`min_length`, `ge`/`le`) and the `Action` enum; an out-of-enum
  action like `set_threshold` fails validation, so the model cannot even express a state change.
- `tools.py`: every tool returns a deep copy; errors are `{"error": ...}` with the valid choices listed
  so a small model can correct itself; `dispatch` checks the allow-list and catches `TypeError` for bad
  arguments.
- `agent.py`: one loop over `max_turns` model calls. Tool turns append the assistant turn and one tool
  message per call. Text turns are validated with `Answer.model_validate_json`; citations must be a
  subset of executed ids (a model citing "c9" is hallucinating evidence). One retry with the error
  message, then `invalid`.
- `router.py`: complex questions go to the cloud only when both flags allow it; otherwise local first,
  cloud as fallback. The cloud run uses `include_local_only=False`, so `get_raw_capture` is neither
  offered nor dispatchable, which is what keeps samples on site even if the cloud model asks for it.

Production: an 8B-class model in Q4 on the level 3 server, measured with the same scenarios plus
latency per answer; the cloud flag owned by OT security with the destination on the proxy allow-list;
OTel spans per model and tool call; alert notes treated as untrusted input (see ai-t1).
