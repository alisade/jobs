# Reference: connect/w5-c1

Reference implementation: `.grading/solution/src/handler.ts`.

Design points an interviewer looks for:

- Small response builders (`elicit`, `delegate`, `close`, `handoff`) so every dialogAction carries
  its required fields; the intent is echoed with the updated slot map (a cleared slot is `null`).
- Validation in the dialog hook, side effects only in the fulfillment hook. `Confirmed` -> `Delegate`
  lets Lex move the intent to `ReadyForFulfillment` and invoke the fulfillment hook.
- `resolvedValues` is the source of truth for custom slot types with TopResolution; when more
  than one value resolves, disambiguate explicitly instead of picking index 0.
- Attempt counters live in session attributes (strings), because the Lambda is stateless and Lex
  only remembers what you return.
- The handoff contract is designed for its consumers: the flow branches on `handoffQueue`
  (Check contact attributes on `$.Lex.SessionAttributes.handoffQueue`), copies `summary`,
  `intent`, `slots` into contact attributes (Set contact attributes) so the agent workspace view /
  screen pop and the ServiceNow incident get them, and `handoffReason` feeds containment
  reporting.
- Prefill from Connect (`callerVerified` + `employeeId`) removes a question for already-identified
  callers; trust it only because the flow set it from a server-side lookup, never from caller input.
- Production: obfuscate EmployeeId in conversation logs (slot obfuscationSetting), runtime hints for
  SystemName, Assisted slot resolution as a retry aid, keep the Lambda warm and fast (voice dead air),
  publish numbered versions behind the `prod` alias, Test Workbench regression sets per release.
