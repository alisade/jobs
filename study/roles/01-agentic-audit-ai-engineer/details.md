# Role 1: AI Engineer, agentic audit controls testing - details

Material for each item in [highlights.md](highlights.md). Shared topics (tool calling, MCP, evals,
security, Python) live in the [shared core](../../shared/details.md) and are not repeated here.
Links were checked on 2026-11-13.

---

## 1. Google's agent stack: Gemini, ADK, Gemini Enterprise Agent Platform

**Why:** "Google Gemini for the LLM, with Gemini Enterprise Agent Platform in scope."

**Naming:** as of 2026-11-13, Google's Vertex AI generative AI and Agent Engine docs redirect to
`docs.cloud.google.com/gemini-enterprise-agent-platform/...`. "Gemini Enterprise Agent Platform" is the
current name for what older material calls Vertex AI (models, Agent Engine, evaluation, grounding). Expect
both names in interviews and tutorials.

**Learn:**
- ADK: agents, tools, sessions and state, multi-agent composition, callbacks for guardrails
- Deploying an ADK agent as a managed service on the platform (formerly Agent Engine): sessions, memory
- Gemini Enterprise: the business-facing app where employees use the agents you deploy
- A2A (agent-to-agent protocol): when one agent needs to call another team's agent

**Links:**
- [Agent Development Kit (ADK) docs](https://adk.dev/)
- [Gemini Enterprise Agent Platform: scale and deploy agents (formerly Agent Engine)](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale)
- [Gemini Enterprise](https://cloud.google.com/gemini-enterprise)
- [A2A protocol](https://a2a-protocol.org/latest/)

**Exercise:** Build an ADK agent with three tools (list tickets, fetch a ticket, fetch a PR) over mock
data. Deploy it to Agent Engine and call it from a Python client.

---

## 2. Stateful orchestration with human review

**Why:** "Build the orchestration layer that lets agents execute reusable skills, manage context and
state, recover from errors, and track execution", with "human review where needed".

**You already have:** Step Functions and pipeline design: retries, idempotency, state between steps.

**Learn:**
- Checkpointing agent state so a run can pause for days waiting for a reviewer
- Interrupt/resume for human approval
- Durable execution for long runs (hundreds of samples), including retries without repeating side effects
- An execution log that records every tool call, input, output and reviewer decision

**Links:**
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph interrupts (human-in-the-loop)](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Temporal docs](https://docs.temporal.io/)
- [Azure Durable Functions overview](https://learn.microsoft.com/en-us/azure/durable-task/durable-functions/durable-functions-overview)

**Exercise:** Add a review gate to the section-1 agent: any "exception" result pauses the run, a reviewer
approves or overrides it, and the run resumes. Kill the process mid-run and show that it resumes cleanly.

---

## 3. Grounding on evidence documents

**Why:** "Make results traceable to supporting evidence." Audit evidence is PDFs, screenshots and
spreadsheet exports.

**Learn:**
- Document parsing: layout, tables, key-value pairs, and keeping page numbers
- Hybrid search (keyword plus vector), chunking that respects tables
- Citations down to the page or cell, and refusing to conclude without evidence
- Gemini grounding options on Vertex AI

**Links:**
- [Azure AI Document Intelligence overview](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview)
- [Azure AI Search: hybrid search](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview)
- [Vertex AI grounding overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/grounding/overview)
- [Contextual retrieval (Anthropic)](https://www.anthropic.com/research/contextual-retrieval)

**Exercise:** Index 20 synthetic evidence PDFs (approval emails, deploy logs). Ask "was change X approved
before deploy?" and return the answer with page-level citations, or "insufficient evidence".

---

## 4. Evals for control testing

**Why:** "Measure accuracy, consistency, cost, and performance against defined benchmarks." General
material is in [shared section 5](../../shared/details.md#5-verification-and-evals).

**Learn:**
- A labeled set per control: samples with known pass/fail/exception outcomes
- Consistency: run each sample N times and report agreement
- Cost and latency per control tested
- Vertex AI's evaluation service for comparing prompts and models

**Links:**
- [Gen AI evaluation service overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-overview)

**Exercise:** Build a 30-sample labeled set for the change-management control and report accuracy,
agreement over 5 runs, and dollars per 100 samples.

---

## 5. Audit domain

**Why:** Preferred: "Familiarity with control design, operating effectiveness, evidence sufficiency,
sampling, and exception documentation."

**You already have:** the auditee side. You know what a change ticket, an access review and a deploy log
look like as evidence.

**Learn:**
- Test of design vs test of operating effectiveness
- Population completeness and accuracy (information produced by the entity, IPE)
- Sampling: sample size by control frequency. A common rule of thumb is about 25 for a daily control and
  2 for a quarterly one; firms set their own tables.
- Exception, deficiency, significant deficiency, material weakness
- ITGC domains: access to programs and data, program changes, computer operations, program development

**Links:**
- [PCAOB AS 2201: audit of internal control over financial reporting](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201)
- [PCAOB AS 2315: audit sampling](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2315)
- [COSO internal control guidance](https://www.coso.org/guidance-on-ic)

**Exercise:** Write a one-page test procedure for the change-management control in auditor language:
objective, population, sample size, attributes tested, and what counts as an exception.

---

## 6. Cross-cloud auth: Azure to Vertex AI

**Why:** "Azure for compute and storage and Google Gemini for the LLM." The Azure workload has to call
Google without long-lived keys.

**You already have:** IAM federation, OIDC trust, and AWS/Azure identity in depth.

**Links:**
- [Workload Identity Federation with other clouds](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-other-clouds)

**Exercise:** From an Azure Function with a managed identity, call Gemini on Vertex AI through Workload
Identity Federation with no service account key.
