# Reference: awsfde/w1-c1

The reference implementation is in `.grading/solution/ask_agent/loop.py` and `costs.py`.

Key points an interviewer looks for:

- **The loop is message bookkeeping.** The assistant message with its `toolUse` blocks goes back
  verbatim, followed by exactly one user message whose content is one `toolResult` per `toolUse`,
  matched by `toolUseId`. Splitting results across messages, or answering only the first of two
  parallel calls, is the classic `ValidationException` ("Expected toolResult blocks at
  messages.N.content for the following Ids ...").
- **Errors are data for the model.** `status: "error"` with a short, actionable text lets the model
  recover ("No shipment SH-99999 for this account"). Unexpected exceptions are logged server-side and
  replaced with a generic message, so internals never reach the model or the user.
- **Tenant comes from the verified context.** The tool schema has `additionalProperties: false`, so a
  forged `tenant_id` fails validation; even if it did not, handlers only read `ctx.tenant_id`. The
  injected argument is logged as a security signal.
- **Guardrail outcome.** With `guardrailConfig` on Converse, an intervention comes back as
  `stopReason: "guardrail_intervened"` with the configured blocked message as the assistant text;
  `trace: "enabled"` adds the assessment so you can tell which policy fired.
- **Bounded loop.** A round limit prevents a model that keeps calling tools from running up cost.
- **Cost.** Sum `usage` across every call in the turn (each round re-sends the growing conversation,
  so input tokens grow per round). Cache read tokens are priced separately; an unknown model must fail
  rather than price at zero.

Production follow-ups: `ConverseStream` for time to first token, a `cachePoint` after the static
system prompt and tools, one retry layer with full jitter for `ThrottlingException`, model invocation
logging, `requestMetadata` (tenant, request id) for per-tenant cost attribution, and a CloudWatch
dashboard on `InvocationThrottles`, `InputTokenCount` and `OutputTokenCount`.
