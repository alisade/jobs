# Reference: fde/w4-c1 trust-advisor

Reference files: `.grading/solution/trust_advisor/{server,redact,policy_lint,hooks}.py`.

Key points:

- **Tools** use `@server.tool(annotations=READ_ONLY, structured_output=True)` with pydantic
  return types; bad input raises `ToolError(...)`, which FastMCP returns as an `isError`
  result. Catch helper-specific errors (`PolicyInputError`, `HooksInputError`) and re-raise
  as `ToolError(str(exc)) from None` so no chained traceback text leaks.
- **explain_decision** builds `DecisionExplanation` field by field: an allowlist, so a new
  column in the vendor export cannot leak. `session_digest = digest(session_id)`.
- **redact_text** applies rules in order: email, `sess-...`, IPv4, card, phone. Card before
  phone because a PAN also matches a long phone pattern; `(?<![\w-])` guards keep
  `hx-1006-000117` intact. Cap after redaction so a cut never splits a match.
- **lint_policy**: length cap before parsing, `yaml.safe_load`, `isinstance(value, bool)`
  checked before the open/closed check (YAML 1.1: `off` -> False), bools excluded from
  numbers (`True` is an `int` in Python).
- **hooks_covered**: regex on the target, allowlist match on module boundaries
  (`m == name or name.startswith(m + ".")`), `importlib.import_module` in a try, then
  `issubclass(cls, StorefrontBackend)`. The concrete backend is the first backend class in
  the MRO that defines a write hook in its own `vars()`; a leaf like `GoodTrusted` that only
  composes does not count (it is a backend subclass by inheritance). Coverage = the
  defining class is a hook mixin in front of the concrete backend.
- **decision_stats**: validate, `store.recent(n, hook)`, nearest-rank p95
  `sorted[ceil(0.95 * n) - 1]`.

Why the allowlist matters: `import_module` executes module top-level code. A "read-only"
tool that imports any dotted path is arbitrary code execution for whoever can call it,
including a model steered by an injected prompt. Annotations are hints to the client, not
enforcement.

Production: put the server behind the week-2 JWT verifier with an audience for this
server and a merchant claim; scope the store by merchant; rate-limit per token; log tool
name, caller and argument digests, never results.
