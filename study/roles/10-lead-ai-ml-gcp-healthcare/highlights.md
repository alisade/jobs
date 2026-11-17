# Role 10: Lead / Senior AI/ML Engineer with GCP (healthcare payer): highlights

The posting is in [posting.md](posting.md). The full material list with links is in [details.md](details.md).
Do the [shared core](../../shared/highlights.md) first. This track only adds what this role needs on top of it.

Two sibling tracks already cover parts of this posting, so this track links to them instead of repeating
them:

- [Role 6](../06-platform-engineer-gcp-terraform/highlights.md) covers GCP foundations, Terraform on GCP,
  IAM, VPCs and the Professional Cloud Architect exam. That is the whole "GCP Cloud Architecture"
  nice-to-have.
- [Role 5](../05-java-fullstack-ai-gemini/details.md) covers Gemini on Vertex AI in production, RAG on GCP,
  FastAPI on Cloud Run, supervised tuning of Gemini, and the Gen AI evaluation service.

What is new here: LangGraph and the other named agent frameworks, the ML side of Vertex AI (Model Garden,
open-model endpoints, Vector Search, Workbench), event-driven pipelines, advanced Python with gRPC, RAG at
much larger scale, the payer domain and its data standards, HIPAA inside AI pipelines, and PEFT/LoRA.

## Where you start

| Posting asks for | You already have |
|---|---|
| "12+ years experience" | 26 years in DevOps and infrastructure. Not 12 years as a software/AI engineer (see the fit note) |
| "3+ years ... production-grade LLM applications, RAG pipelines, or autonomous agent frameworks" | Not yet. Heavy daily Claude Code use with your own harness (skills, hooks, MCP servers) is real agent work, but it is not a production LLM application you shipped to users |
| Multi-agent orchestration, tool calling, stateful graphs, memory (LangGraph, AutoGen, LlamaIndex, Semantic Kernel) | Tool calling, MCP servers and permission design from your Claude Code harness; Step Functions for stateful, retryable workflows. None of the four named frameworks |
| Vertex AI (Model Garden, endpoints, Vector Search, Workbench) | Not yet. You run managed compute, quotas and endpoints on AWS, so the operating model is familiar |
| Cloud Run, Pub/Sub, Cloud Functions | Lambda, Step Functions, Kinesis/Firehose, EKS and Docker in production. Same event-driven shapes on a different cloud |
| Advanced Python (AsyncIO, FastAPI, Pydantic, gRPC), tested and containerized | Some Python, mostly for ops; TypeScript and bash daily; Docker and CI/CD in depth. Advanced async Python services and gRPC are not on your record |
| Payer workflows: prior authorization, claims, appeals, member engagement | Not yet. You have worked in mortgage servicing, which is also a regulated, document-heavy, deadline-driven back office |
| FHIR, EDI X12, ICD-10/CPT | You have operated EDI integrations at the infrastructure level. FHIR, the healthcare X12 transactions and the code sets are new |
| Vector indexing, hybrid search, reranking, chunking at scale | Not yet beyond the shared baseline |
| HIPAA compliance, PHI handling, privacy in AI pipelines | Years in regulated environments: federal (GSA, NIST 800-53, FISMA) and mortgage servicing (SOX). Least privilege, audit trails, approval gates, change control. HIPAA itself is new, but the control mindset transfers |
| Terraform, GCP VPCs, IAM (nice-to-have) | Terraform through Spacelift, deep AWS and Azure IAM and networking. GCP itself is covered in role 6 |
| PEFT, LoRA fine-tuning (nice-to-have) | Not yet |
| Automated LLM benching, CI for probabilistic software (nice-to-have) | CI/CD is your day job. The eval method is in the shared core |
| GCP Professional ML Engineer or Professional Cloud Architect (nice-to-have) | Not yet |

## Honest fit note

- **Two hard filters, and study does not clear either one.** "12+ years ... of software/AI engineering"
  and "3+ years directly building, deploying, and maintaining production-grade LLM applications, RAG
  pipelines, or autonomous agent frameworks". Your 26 years are infrastructure and DevOps years. A
  recruiter who reads the minimums literally will likely stop there. Do not stretch either number on the
  resume. What you can honestly say: 26 years of production engineering, years of automation code in
  TypeScript, bash and Python, and agent work in your own daily harness. Then point at one deployed,
  public system (the portfolio below) as your production LLM evidence.
- **Payer domain is a strong preference, not a footnote.** "Proven familiarity" with prior authorization,
  claims, appeals and member engagement will separate candidates. Teams like this often hire people who
  already speak X12 and FHIR. You can learn the vocabulary and the CMS rule in a few weeks, which is
  enough to hold a conversation, but say plainly that you have not worked at a payer.
- **Regulated-environment operations is a real asset here.** Most AI engineers have never had to show an
  auditor who accessed what, prove least privilege, or run change control. HIPAA's Security Rule asks for
  exactly that: access control, audit controls, integrity, transmission security. Your federal and SOX
  work is the strongest card you have for this posting. Lead with it in the HIPAA conversation.
- **How to target each level.**
  - **Senior** is the realistic target. It is mostly hands-on build: agents, retrieval, Python services,
    evals. Apply as Senior once the portfolio is deployed and you can walk through its code line by line.
  - **Lead** adds architecture ownership and leading other engineers. Your production leadership (P1
    command, platform design, approval gates, mentoring) fits the "lead" half, but a Lead AI/ML title
    with no shipped LLM product is a hard sell. Apply for Lead only if the recruiter says the team needs
    someone to own platform, security and delivery for the AI work, and frame yourself that way: the
    person who makes the agents safe, observable and compliant in production.
  - Ask the recruiter: "Is the 3+ years of production LLM work a hard cutoff for the Senior level, or
    would a deployed portfolio system plus long production experience in regulated environments be
    considered?" and "Which payer workflow does the team work on first: prior authorization, claims or
    appeals?"
- **The posting names AutoGen and Semantic Kernel, and both have changed.** AutoGen is archived and
  Semantic Kernel now points to Microsoft Agent Framework as its successor. Knowing this, and saying it
  calmly in an interview, is a cheap way to show you are current. Go deep on LangGraph; know the others
  at positioning level (details section 2).

## Gaps, most important first

1. **Production LLM application evidence.** The 3+ years filter. Only a deployed, measured, public
   system narrows it.
2. **LangGraph.** Stateful graphs, checkpointing, interrupts for human review, memory, multi-agent
   patterns. The framework you will be asked to whiteboard.
3. **Advanced Python services.** asyncio, FastAPI, Pydantic v2, gRPC, pytest, containers. The posting says
   "advanced"; this is where a coding interview will test you.
4. **Payer domain.** Prior authorization (including the CMS Interoperability and Prior Authorization
   Final Rule), claims lifecycle, appeals, member engagement.
5. **Health data standards.** FHIR R4, the Da Vinci PAS, CRD and DTR guides, X12 837/835/278,
   ICD-10-CM/PCS, CPT.
6. **RAG at scale.** Vector indexing, hybrid search, reranking, chunking for large policy document
   stores, retrieval evals.
7. **Vertex AI for ML engineering.** Model Garden, deploying open models to endpoints, Vector Search,
   Workbench. Google now documents this under "Gemini Enterprise Agent Platform".
8. **HIPAA inside AI pipelines.** PHI flow, minimum necessary, BAA scope, de-identification with the
   Healthcare API and Sensitive Data Protection, audit logging.
9. **Event-driven pipelines on GCP.** Cloud Run, Pub/Sub, Cloud Run functions, Eventarc.
10. **PEFT/LoRA fine-tuning** of a small model for extraction or classification.
11. **Certification.** Professional Machine Learning Engineer fits this posting better than Cloud
    Architect.

GCP foundations and Terraform are not on this list because [role 6](../06-platform-engineer-gcp-terraform/details.md)
covers them, and evals in CI are mostly method from the [shared core](../../shared/details.md#5-verification-and-evals).

## Plan (after the shared core)

Ten weeks at roughly 10 to 15 hours per week. Python and the payer domain start in week 1 and run in
parallel, because they are the slowest to build credibility in. Book the Professional Machine Learning
Engineer exam in week 1 for around week 10.

| Week | Focus | Output |
|---|---|---|
| 1 | Advanced Python: asyncio, Pydantic v2, FastAPI. Payer reading: PA, claims, appeals, CMS-0057-F | A FastAPI service with async I/O, typed models and 20+ pytest tests. A one-page payer glossary in your own words |
| 2 | gRPC in Python, containers, Cloud Run, Pub/Sub, Cloud Run functions. GCP project setup from role 6 in Terraform | Two services talking gRPC, one stage triggered by Pub/Sub, all on Cloud Run from Terraform |
| 3 | FHIR R4, Da Vinci PAS/CRD/DTR, X12 278/837/835, ICD-10 and CPT. Generate Synthea patients | A FHIR store in the Healthcare API loaded with synthetic patients, and a PAS-shaped request built from one |
| 4 | LangGraph: state, nodes, edges, checkpointer, interrupts, memory | A single-agent PA intake graph that pauses for review and survives a process kill |
| 5 | LangGraph multi-agent, tool calling, subgraphs. Positioning of LlamaIndex and Microsoft Agent Framework | The multi-agent flow: intake, policy retrieval, criteria check, draft determination |
| 6 | RAG at scale: chunking, Vector Search index, hybrid dense plus sparse, ranking API, retrieval evals | Policy retrieval over a large synthetic policy corpus, with recall@k before and after reranking |
| 7 | Vertex AI ML side: Model Garden, deploy an open model to an endpoint, Workbench | A Gemma or similar open model on a Vertex endpoint, called from the graph, with cost per call logged |
| 8 | HIPAA in the pipeline: PHI map, de-identification, audit logs, BAA scope, VPC-SC basics | A data-flow diagram that marks every place PHI exists, plus de-identified copies for evals and logs |
| 9 | PEFT/LoRA: tune a small model for ICD-10-CM code extraction, compare with prompting | A tuning report: accuracy, latency and cost per 1,000 notes for LoRA vs prompt-only |
| 10 | Evals in CI, polish, demo video, exam | Eval gate that fails the build on regression; README with results; certification exam |

## Portfolio project: prior-authorization assistant on GCP

One public repo, synthetic data only, that touches every must-have in the posting:

- **Data:** synthetic patients from Synthea loaded into a Cloud Healthcare API FHIR store, and a set of
  synthetic medical policies written in the style of a payer's coverage criteria (thousands of pages, so
  retrieval is a real problem). Use ICD-10-CM codes, which are public. Do not publish CPT descriptors,
  which are licensed by the AMA; refer to procedures by HCPCS Level II or by a generic label.
- **Intake:** a FastAPI endpoint that accepts a PA request shaped like a Da Vinci PAS bundle (Claim plus
  supporting resources), validates it with Pydantic, and publishes it to Pub/Sub.
- **Agents:** a LangGraph flow with an intake agent, a policy retrieval agent, a criteria-check agent that
  uses tool calls against the FHIR store (diagnoses, prior therapies, labs), and a drafting agent that
  writes a determination with a citation for every criterion. Checkpointed in Postgres so a case can wait
  days for a reviewer.
- **Human in the loop by design:** the system may only recommend approval. Every denial, every low-confidence
  case and every missing-information case routes to a human reviewer through a LangGraph interrupt. The
  reviewer's decision and reason are stored. "A model never denies care on its own" is the design rule
  to state in an interview; then ask how the team's compliance group reads current CMS and state
  guidance on algorithm-assisted denials.
- **Clock:** every case records its CMS-0057-F decision deadline (72 hours expedited, 7 calendar days
  standard) and a dashboard shows time remaining. A specific denial reason is required before a case can
  close.
- **Retrieval:** chunking that keeps policy section structure, Vertex AI Vector Search with hybrid dense
  plus sparse, the ranking API as a reranker, metadata filters by line of business and effective date.
- **Services:** FastAPI for the edge, gRPC between internal stages, all on Cloud Run with separate service
  accounts and no public ingress except the edge.
- **PHI handling:** a PHI data-flow map, Healthcare API and Sensitive Data Protection de-identification for
  every copy that leaves the FHIR store (eval sets, logs, traces), Data Access audit logs turned on, and a
  short "if this were real" section that lists the BAA, covered services and regions you would need.
- **Evals in CI:** retrieval recall@k, citation accuracy (does each cited chunk support its criterion),
  criteria accuracy against a labeled set, and a check that no denial ever bypasses review. The build
  fails on regression.
- **Small model:** a LoRA-tuned small open model for ICD-10-CM code extraction from synthetic notes,
  compared against prompting a large model on the same held-out set for accuracy, latency and cost.
- **Infrastructure:** Terraform for the whole GCP setup (projects, VPC, service accounts, Healthcare API
  dataset, Pub/Sub, Cloud Run, Vector Search index), applied from CI with Workload Identity Federation, as
  in role 6.

Keep it cheap: small endpoints that you undeploy after each session, and a `make destroy`. No real PHI,
no employer specifics, no real payer's policies copied in.

## One-line pitch

"I have spent 26 years running production systems under federal and SOX audit; I built a prior
authorization assistant on GCP with LangGraph, hybrid retrieval and a human on every denial, and I know
how to make an AI pipeline that handles PHI pass a security review."
