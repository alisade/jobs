# ms/w10-t1: HR agent starts a leave request when asked for a balance

Type: troubleshooting. Estimate: 1.5-2 h. Exam: AB-100 - Deploy AI-powered business solutions (40-45%): monitor, analyze and tune agents, test AI solutions; also AB-400 Copilot Studio agent objectives.

## Scenario

Litware runs **HR Assist**, a Copilot Studio agent in Microsoft Teams with generative orchestration on.
It has two Workday connector tools, a Holiday calendar topic and two SharePoint knowledge sources.
Solution 1.8.0.0 went to production on 2026-10-02 through the `hr-agents-prod` pipeline.

The ticket, as HR Operations filed it:

> Since last Thursday, employees who ask HR Assist in Teams how many vacation days they have left are
> asked "What is the first day of your leave?" and then "How many hours...". Most give up. HR inbox
> volume for balance questions is up 3x. Two people say the agent "almost booked a holiday" for them.
> Nothing was changed on our side except adding the new leave request feature. Fix before payroll
> cut-off on Friday.

## Your task

1. `make setup` builds `incident/`: activity-map reconstructions of production conversations, analytics
   exports, the last regression test-set run, knowledge indexing logs and the solution history.
2. Find the root cause using the evidence and the agent definition under `agent/` (code-editor YAML of the
   tools and topic; simplified exports of settings and knowledge sources).
3. Fix the agent definition. Keep both tools (same connector operations) and the other components.
4. Write `ANSWER.md`: root cause with evidence (file names and excerpts), the fix, how you verified it,
   and how you would stop this class of regression reaching production.

### About the tests: a proxy, not the real orchestrator

The real generative orchestrator is an LLM. It chooses topics, tools and knowledge mainly from their
**descriptions**, and also uses names and input names/descriptions. Offline we cannot run it, so
`tests/proxy_router.py` scores the same text with TF-IDF cosine similarity. Its limits, by design:
no synonyms (use the words users use, which Learn recommends anyway), sentences with negation are ignored
(write "does not ..." sentences for the real model; they cannot hurt you here), and one component per
utterance. If a description you believe is genuinely good fails the proxy, say so in ANSWER.md; the
grader weighs your reasoning.

## Acceptance criteria

- The routing regression set (balance, submit, holiday and policy questions, including paraphrases you have
  not seen) routes to the right component.
- Tool display names and descriptions are distinct and specific; each says what it does, when to use it,
  and what it does not do (60-500 characters, no keyword stuffing: no word more than 3 times).
- Every automatically filled tool input has a description (20+ characters).
- `ANSWER.md` explains the root cause with evidence, separates it from anything in the bundle that is
  not the cause, and proposes a guard for future releases.

## How to run

```
make setup   # uv sync, then generate incident/
make test    # visible slice of the regression set
make clean   # remove .venv and incident/
```

Then from the workbooks root: `/grade ms/w10-t1`.

## What to submit

Your edits under `agent/` and `ANSWER.md`.

## Study guide links

- [Week 10 Wed - Monitor, analyze, tune](../../../../microsoft-adf-powerapps-study-plan.html#week10)
- [Week 10 Thu - Testing AI solutions](../../../../microsoft-adf-powerapps-study-plan.html#week10)
- [Orchestrate agent behavior with generative AI (authoring descriptions)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-generative-actions)
- [Review agent activity (activity map)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-review-activity)
- [Add tools to custom agents](https://learn.microsoft.com/en-us/microsoft-copilot-studio/add-tools-custom-agent)
- [Copilot Studio analytics](https://learn.microsoft.com/en-us/microsoft-copilot-studio/analytics-overview)
