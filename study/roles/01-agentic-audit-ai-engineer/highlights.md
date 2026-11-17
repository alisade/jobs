# Role 1: AI Engineer, agentic audit controls testing - highlights

Posting: [posting.md](posting.md). Full material: [details.md](details.md).
Do the [shared core](../../shared/highlights.md) first.

Earlier write-ups for this role, in this folder:
[learning plan PDF](AI-Engineer-Agentic-Audit-Learning-Plan.pdf),
[highlights deck](AI-Engineer-Agentic-Audit-Highlights.pptx),
[highlights PDF](AI-Engineer-Agentic-Audit-Highlights.pdf),
[highlights web page](AI-Engineer-Agentic-Audit-Highlights.html).

## Where you start

| Posting asks for | You already have |
|---|---|
| Scoped permissions, approval gates, auditable agent activity | Change management, Spacelift approvals, PIM, least-privilege IAM |
| Orchestration, error recovery, execution tracking | Step Functions, pipelines, Jenkins |
| AI harnesses that load and execute reusable skills | Your Claude Code setup |
| Familiarity with SOX/ITGC testing | The auditee side: SOX-relevant work at Lakeview, FISMA/NIST 800-53 at GSA |
| Azure compute and storage | Lakeview Azure work |

**Fit:** good. The gaps are building agents in code (rather than configuring them), Google's agent stack,
RAG with citations, and the auditor's vocabulary.

## Gaps, most important first

1. **Production Python agent services.** Covered in the shared core ([section 3](../../shared/details.md#3-tool-calling-and-structured-outputs)).
2. **Google's agent stack.** Gemini, ADK, and Gemini Enterprise Agent Platform (the current name for
   Vertex AI's model and agent platform, including what was Agent Engine).
3. **Stateful orchestration with human review.** Checkpoints, interrupt/resume, durable execution.
4. **Grounding on evidence documents.** Document Intelligence, Azure AI Search, citations to the page or cell.
5. **Evals** (shared [section 5](../../shared/details.md#5-verification-and-evals)), applied to control testing: accuracy and consistency per control.
6. **Audit domain.** Design vs operating effectiveness, IPE, sampling, deficiency levels.
7. **Cross-cloud auth.** Azure workloads calling Vertex AI through Workload Identity Federation.

## Plan (after the shared core)

| Week | Focus |
|---|---|
| 1 | Gemini SDK and ADK: build a 3-tool agent with structured output |
| 2 | Human-in-the-loop and state: LangGraph interrupts or ADK sessions; Agent Engine deploy |
| 3 | Evidence RAG: Document Intelligence, AI Search, page-level citations |
| 4 | Evals per control, tracing, cost; prompt-injection test through an evidence file |
| ongoing | ITGC/SOX reading, an hour or two a week |

## Portfolio project: ITGC change-management control tester

1. Pull a population of merged PRs and change tickets.
2. Draw a sample sized to the control frequency.
3. For each item, have an agent check: approval before deploy, linked ticket, approver is not the author, tests passed.
4. Stop at a human review gate for every exception.
5. Produce a workpaper where every conclusion cites its evidence.
6. Report accuracy, consistency and cost per control from an eval suite.

Stack: Gemini, ADK, Pydantic, on Azure. Public repo, synthetic or open-source data only.

## Pitch

"I make agents safe and operable in production: write tools behind approval gates, and a trail
an auditor can follow to reconstruct what the agent did."
