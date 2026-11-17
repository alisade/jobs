# Role 3: AI Engineer, GenAI / Agentic Development (highlights)

Posting: [posting.md](posting.md). Full material with links: [details.md](details.md).
Do the [shared core](../../shared/highlights.md) first. This track only covers what the shared core does not.

## Where you start

| Posting asks for | You already have |
|---|---|
| "Expert-level experience with AI coding assistants and agentic development workflows" | Daily Claude Code use with your own harness: CLAUDE.md rules, skills, hooks, MCP servers (Jira, Spacelift, AWS), permission modes |
| "Deploy production-grade ... applications", "testing, deployment, and optimization" | 26 years of CI/CD, EKS, Lambda, Step Functions, Helm, ArgoCD, Jenkins, CodeBuild |
| "Work across different codebases, technology stacks, and AI platforms" | AWS and Azure, Linux and Windows, Kubernetes fleets, Terraform via Spacelift, AD/LDAP/Kerberos |
| "Modern cloud-based AI platforms and services" (preferred) | Deep AWS, which is where Bedrock and AgentCore live; the shared core adds Gemini/Vertex |
| "Strong ownership, prioritization, and execution" | Production incidents and P1s, end to end |
| TypeScript | CDK in TypeScript every day |
| Python | Some Python |
| "Agile/Scrum ... Jira and Confluence" | Daily Jira and Confluence-style workflows |
| Reliability half of "bias, safety, reliability" | Observability, approval gates, backups before mutation, scoped permissions |

## Honest fit note

This is an application engineer role with a GenAI focus, not a platform or DevOps role. The posting's core
is "full-stack ... Python, TypeScript, React", "microservices", and "2+ years focused on AI/ML or Generative AI
applications". Your strongest material (deploying, operating and securing systems, and running an agent
harness) covers the edges of this job, not its centre.

Where you are a stretch:

- **React and front-end work.** Not in your known background. Treat it as a real gap, not a refresher.
- **Application-level backend code.** You write TypeScript for infrastructure (CDK) and scripts in bash and
  Python. Writing a service with a data model, an API contract, business logic and tests is a different
  muscle. Depth here is unknown, so assume a gap.
- **"2+ years focused on AI/ML or Generative AI applications".** Your AI work is heavy and real, but it is
  tooling for your own engineering, not shipped AI products for users. Do not claim otherwise. Frame it
  as "agentic development workflows in production use" and back it with the portfolio project.
- **Responsible AI vocabulary.** You practise the reliability and safety side. Bias, fairness and model
  documentation are new.
- **Retail.** No known retail experience. It is only preferred, so learn the common use cases and move on.

The pitch that works: someone who can ship a GenAI app all the way to production and keep it running, and
who already uses agentic coding at an expert level. Expect a live coding or take-home round in Python or
React. Prepare for that specifically.

## Gaps, most important first

1. **React + TypeScript front end.** Components, state, data fetching, streaming a model response into
   the UI, front-end tests. The posting names React twice.
2. **Application backend in Python.** FastAPI services with a real data model, async I/O, dependency
   injection, pytest, and a typed API contract shared with the front end.
3. **Production GenAI app engineering.** Streaming, retries and fallbacks, rate limits, prompt caching,
   cost and latency budgets, tracing, and an LLM gateway layer. You know the ops side; learn the app side.
4. **Microservices design and trade-offs, argued at the whiteboard.** You have run microservices; now
   practise defending the boundaries, sync vs async calls, data ownership, and when a monolith is better.
5. **Responsible AI.** Bias testing, safety guardrails, human oversight, model and system cards, NIST AI
   RMF terms. Be able to describe what you would actually build, not only the principles.
6. **Integrating GenAI and agents into existing enterprise apps.** Strangler-style rollout, feature flags,
   human fallback, and agent frameworks you may be asked about (ADK, LangGraph, AgentCore, A2A).
7. **Retail domain.** Product search, catalog enrichment, customer service, store operations, and the
   metrics retailers care about.
8. **Mentoring and technical leadership, told as stories.** ADRs, coding standards for AI-assisted code,
   and explaining AI to non-technical stakeholders.

## Six-week plan (after the shared core)

| Week | Focus | Output |
|---|---|---|
| 1 | React + TypeScript fundamentals; Vite; TanStack Query; testing library | A small React app that lists products from a mock API, with tests |
| 2 | FastAPI service: data model, async, pytest, OpenAPI to TypeScript types | Catalog service with CRUD, search and tests, its types generated into the React app |
| 3 | GenAI service: streaming, tool calls, retries, caching, cost logging | Assistant service that streams answers into the React UI over SSE |
| 4 | Evals, guardrails and responsible AI: bias probes, refusal tests, grounding checks | Eval suite in CI, plus a one-page system card |
| 5 | Microservices deployment, tracing, load and failure testing | All services on Kubernetes or ECS with traces and a cost dashboard |
| 6 | Retail framing, ADRs, mentoring stories, mock interviews (whiteboard plus live coding) | Write-up and demo video for the portfolio project; 6 STAR stories |

## Portfolio project: a retail shopping assistant, built as microservices

A small, public, full-stack GenAI app for a fake store. It shows the exact stack the posting names.

- **Front end:** React + TypeScript (Vite). Product grid, a chat panel that streams answers, product cards
  rendered from structured tool output, and a "talk to a human" handoff button.
- **Catalog service:** Python FastAPI with Postgres. Products, inventory and orders; OpenAPI contract
  turned into TypeScript types for the front end.
- **Assistant service:** Python FastAPI agent with tools: `search_products`, `check_inventory`,
  `get_order_status`, `start_return`. Read-only tools by default; `start_return` needs user confirmation in
  the UI. Uses Claude, with a fallback model on another provider behind a thin gateway interface.
- **Evals and guardrails:** promptfoo or pytest suite in CI: answer grounding (no invented products or
  prices), refusal on out-of-scope requests, prompt injection through a product review, and paired bias
  probes (same request, different customer names or dialects, compare recommendations and tone).
- **Operations:** Docker Compose locally, Helm on Kubernetes (or CDK on ECS) for the real deploy,
  OpenTelemetry traces with token cost per request, and a short system card covering intended use,
  known limits and the bias test results.
- **Write-up:** three ADRs (service boundaries, sync vs streaming, model fallback) and a README that
  explains trade-offs to a non-technical reader.

Keep it free of any GSA or Lakeview specifics.

## One-line pitch

"I ship GenAI apps the way I have shipped production systems for 26 years: React and Python services on a
platform I can operate, evals and guardrails in CI, and an agentic workflow I already use at an expert
level every day."
