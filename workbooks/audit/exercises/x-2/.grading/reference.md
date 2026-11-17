# Reference: audit/x-2

A model answer is in `.grading/solution/DESIGN.md` and `solution/ANSWER.md`. Other designs can score
full marks if each committee condition and standard is met by a named mechanism.

What separates strong answers:

- **State and evidence stay in the audited estate.** Hosting orchestration on Azure with durable
  state, an immutable log and WORM Blob satisfies C3 and SEC-07 directly; hosting the agent on
  Google's managed runtime is defensible only if the answer shows how logs and state reach MFH's
  immutable storage.
- **No keys, concretely.** Managed identity token exchanged at Google STS through a workload
  identity pool provider with an attribute condition on the identity, plus an org policy blocking
  service account key creation.
- **Write tools behind approval, none in the evidence reader.** This is how the lethal trifecta is
  broken by design rather than by prompt wording.
- **ControlPilot under CM-03.** The strongest answers notice that the tool is itself a program
  change subject: prompts and model versions are code, released with an independent approver and
  an eval gate, and a provider model deprecation is a change.
- **Cost honesty.** Model tokens are about $12 a year at illustrative prices for the stated volumes;
  infrastructure and reviewer time dominate. Answers that present token cost as the driver have not
  done the arithmetic.

Interview angle: "Why not just deploy the ADK agent to the managed agent runtime and be done?" and
"How does an external auditor re-perform an item ControlPilot tested?"
