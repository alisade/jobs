# Reference: backend/x-1 Timed whiteboard: a self-serve workflow automation service

The model whiteboard is in `.grading/solution/DESIGN.md`. Key moves an interviewer looks for:

- **Do not rebuild the engine.** Temporal is given. The platform's value is the paved road: typed
  primitives with good defaults, a start/signal/query API, triggers from domain events, isolation and
  quotas, and observability. Product teams either compose primitives or ship their own workflow code
  in their own task queue with the platform SDK wrapper.
- **Triggers are consumers.** A trigger service consumes domain events (already produced through the
  outbox) and starts workflows with a workflow id derived from the event id, so redelivery and replays
  are idempotent (Temporal rejects a duplicate workflow id while one is running, and the id reuse
  policy covers completed ones).
- **Long waits are cheap, long histories are not.** 180,000 renewal workflows waiting on timers is fine;
  a workflow that loops for months must continue-as-new.
- **Agents propose, people approve.** The agent starts the approval with the user's identity and can
  query status; it has no update handler permission for "approve".
- **Versioning is an operational practice:** patch markers or worker versioning, plus replay tests on
  recorded histories in CI before a deploy.

## Interview angles
- "Why not let teams write Temporal workflows directly and skip the primitives?" (They will, for
  complex cases; the primitives are for the 80% and carry the guard rails.)
- "How do you know a workflow is stuck vs waiting?" (Search attributes for state, an SLA timer that
  raises an alert, dashboards on schedule-to-start latency and open executions per type.)
