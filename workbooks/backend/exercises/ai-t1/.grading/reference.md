# Reference: backend/ai-t1 The assistant showed another business unit's pipeline

Injected fault: `get_account_timeline` takes `tenant_id` from the tool arguments (`args.get("tenant_id")
or session.tenant_id`) and its schema invites the model to use it. An injected instruction in a
bu-amer activity note made the model pass `tenant_id=bu-emea`. The audit log was too thin to
reconstruct the session. Fixed tools in `.grading/solution/assistant_tools/tools.py`, model answer in
`.grading/solution/ANSWER.md`.

The principle: tool scoping and delegated identity are the control; model behavior is not. Treat the
model as an untrusted caller acting for a user, never broader than that user, and treat record text as
untrusted data (the lethal trifecta: private data, untrusted content, a way to send it out).

## Interview angles
- "Would you let an agent use a service account with read-all?" (No: delegated user identity, so RLS and
  audit apply as for the user.)
- "How would you test this?" (Injection eval cases in CI: notes with instructions, expected tool calls,
  assert no cross-tenant or write calls.)
- "Partner managers need cross-BU reads. How?" (A role in the delegated token that a policy honors,
  never a tool argument.)
