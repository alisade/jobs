# Shared core: highlights

These skills serve both target roles. Do this track first, because each role track builds on it.
The full material list with links is in [details.md](details.md).

## Where you start

You have 26 years of DevOps experience and use Claude Code heavily every day. Several things you already do
map straight onto what both postings ask for:

| Posting asks for | You already have |
|---|---|
| Reusable agent skills, a skills harness | A daily Claude Code setup with CLAUDE.md rules, skills, hooks, MCP servers and permission modes |
| Human approval and verification points | Change management, Spacelift approval policies, PIM elevation, "back up before mutate" discipline |
| Scoped permissions, auditable activity | Least-privilege IAM, EKS access entries, pre-push hooks that enforce policy |
| Production incidents, root cause, systems thinking | 26 years of P1s across AWS, Azure, Kubernetes, Jenkins, AD |
| CI/CD, Git, observability, secure delivery | Your day job |

What's missing is mostly framing plus a few hands-on builds. You have to show that you design agent
workflows deliberately rather than only use them.

## The eight shared skills, most important first

1. **Agentic coding tools as an engineering platform.** Know Claude Code skills, subagents, hooks, MCP,
   permissions, headless mode and the Agent SDK well enough to design them for a team, not just for yourself.
2. **Agent design patterns.** Workflows vs agents, routing, orchestrator-workers, evaluator-optimizer,
   and context engineering, meaning what goes into the context window and why.
3. **Tool calling and structured outputs.** JSON schemas, Pydantic models as contracts, and validation with
   retry on bad output, with both Claude and Gemini.
4. **MCP.** Build at least one MCP server yourself, so that "tool integration" is something you've done
   rather than something you've read about.
5. **Verification and evals.** Separate "the model said so" from "we verified it": golden datasets,
   LLM-as-judge, deterministic checks, and approval gates.
6. **LLM security.** Prompt injection (especially through files the agent reads), the "lethal trifecta",
   tool scoping and sandboxing.
7. **Spec-driven development.** Write the spec first, have the agent implement it, then verify against
   the spec. Role 2 leans on this heavily; role 1 uses it for skills.
8. **Python plus Gemini/Vertex basics.** Both postings name Google's AI stack. Python is required for role 1
   and preferred for role 2.

## Four-week shared plan

| Week | Focus | Output |
|---|---|---|
| 1 | Claude Code deep dive: skills, subagents, hooks, headless, Agent SDK | A written design of your current setup, framed as a team harness |
| 2 | Agent patterns, tool calling, structured outputs (Claude + Gemini), Pydantic | A small CLI agent that calls 3 tools and returns validated JSON |
| 3 | MCP server build, evals, prompt-injection testing | An MCP server and an eval suite for the week-2 agent |
| 4 | Spec-driven development, then the portfolio piece below | A public skills repo |

## Shared portfolio piece: a public skills repo

Publish a repo of 4-6 Claude Code skills plus hooks that encode the discipline you already practice.
Examples: "back up live state before mutation", "pre-push attribution scan", "verify before claiming done",
"triage an unfamiliar repo". Each skill comes with:

- a `SKILL.md` that has clear trigger conditions
- an explicit verification step and a human approval point
- a short eval: 5-10 cases showing it triggers when it should and refuses when it should

Both roles ask for this directly. Role 1 wants "AI harnesses that load and execute reusable skills" and
role 2 wants people who "design, author, refine, and govern reusable skills and agents". Do not include
any GSA or Lakeview specifics in it.

## One-line pitch for both roles

"I have run production systems for 26 years, and I build agent workflows the way I build production
automation: scoped permissions, approval gates, verification before claims, and a trail an auditor
can follow."
