---
title: "AI Engineer (Agentic Audit Controls Testing) - Learning Plan"
date: "2026-11-13"
---

Most of what this job asks for is closer to what you already do than it looks. The gaps fall into three groups: LLM application engineering, agent orchestration patterns, and audit domain vocabulary. Infrastructure, security, CI/CD and enterprise integration you already have.

## What already transfers

- **Approval gates, scoped permissions, auditable activity.** You run these every day: change management, Spacelift approval policies, PIM elevation, least-privilege IAM. Agents need the same things.
- **Orchestration, retries, state, idempotency.** Step Functions, pipelines and Jenkins are all multi-step workflows that recover from errors. An agent workflow is that plus a non-deterministic step in the middle.
- **Skills harness.** Your Claude Code setup (CLAUDE.md rules, skills, hooks, MCP servers, permission modes) is a harness that loads and runs reusable skills. Treat it as real experience and describe it that way in interviews.
- **The auditee side of ITGC.** At Lakeview (SOX-relevant mortgage servicing) and GSA (FISMA/NIST 800-53) you have produced evidence for change management and access reviews. You know what auditors ask for.

## Gaps, most important first

1. **Production Python for LLM backends**
    - FastAPI, async, and Pydantic models used as the contract for structured outputs.
    - The google-genai SDK: function calling, `response_schema`, token counting, context caching.

2. **Agent orchestration frameworks**
    - **Google ADK** (Agent Development Kit) and **Vertex AI Agent Engine**. Learn these first, since "Gemini Enterprise Agent Platform" is Google's agent stack. Google has renamed these products several times, so check the current docs for exact names.
    - **LangGraph**, for the general concepts: graph state, checkpointing, interrupt/resume for human review.
    - Durable execution for long jobs: Temporal or Azure Durable Functions.
    - **MCP** for exposing tools, and **A2A** (agent-to-agent protocol) for multi-agent setups.

3. **Grounding and RAG**
    - Document parsing with Azure AI Document Intelligence. Audit evidence is PDFs, screenshots and Excel exports.
    - Chunking, embeddings, Azure AI Search with hybrid search.
    - Citations that point to the exact page or cell. "Results traceable to supporting evidence" means every conclusion links back to its source.

4. **Evaluations.** This separates hobbyists from people who get hired.
    - Golden datasets, LLM-as-judge, and consistency checks (run the same input N times and measure variance).
    - Cost and latency tracking per run, plus eval regressions gated in CI.
    - Tools: promptfoo or DeepEval, the Vertex AI Gen AI evaluation service, Langfuse or OpenTelemetry GenAI tracing.

5. **LLM-specific security**
    - Prompt injection through retrieved documents. An evidence file can carry instructions.
    - Read-only versus write tools, sandboxed code execution for population analysis, PII handling.
    - Cross-cloud auth from Azure to GCP via Workload Identity Federation. You will pick that up fast.

6. **Audit domain vocabulary**
    - Test of design versus operating effectiveness.
    - Population completeness and accuracy (IPE).
    - Sample sizes by control frequency (for example, a common rule of thumb is about 25 samples for a daily control, 2 for a quarterly one).
    - Evidence sufficiency, exception versus deficiency versus significant deficiency versus material weakness.
    - The ITGC domains: access, change, operations, SDLC.
    - Sources: ISACA's ITGC material, PCAOB AS 2201, and any Big 4 SOX/ITGC primer.

## One portfolio project covers almost all of it

Build an **ITGC change-management control tester**:

1. Pull a population of merged PRs and change tickets.
2. Draw a statistical sample.
3. For each sample, have an agent check: was it approved before deploy, is a ticket linked, is the approver different from the author (segregation of duties), did tests pass.
4. Pause at a human review checkpoint for exceptions.
5. Output a workpaper where every conclusion cites its evidence.
6. Add an eval suite that reports accuracy, consistency and cost per control tested.

Build it with Gemini, ADK and Pydantic, run it on Azure, and put it in a public repo. Use synthetic or open-source repo data, not GSA or Lakeview data. It is exactly what the posting describes, and it is a story you can tell from the auditee side.

## Rough timeline

| Weeks | Focus |
|---|---|
| 1-2 | Gemini SDK, tool calling, structured outputs, Pydantic, FastAPI |
| 3-4 | ADK or LangGraph, state, human-in-the-loop, error recovery; start the project |
| 5 | RAG over evidence documents, citations, Document Intelligence |
| 6 | Evals, tracing, cost tracking, prompt-injection hardening |
| ongoing | ITGC/SOX reading, an hour or two a week |

## Interview positioning

Position yourself as the person who makes agents safe and operable in production. Most applicants can make a demo work. Few can explain why the agent's write tools sit behind an approval gate and how an auditor would reconstruct what it did.
