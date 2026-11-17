# ms/w9-c1: Copilot Studio topics in YAML - password reset, fallback and escalation

Type: coding. Estimate: 2 h. Exam: AB-100 - Design AI and agent solutions (25-30%): topics, fallback and generative orchestration; also AB-400 agent objectives.

## Scenario

Litware runs an IT Service Desk agent in Copilot Studio (Teams channel, generative orchestration on).
The pilot went badly:

- "Reset my password" sometimes reset a colleague's account, because nobody asked whose account it was.
- Users who typed something the agent did not understand got "Could you rephrase?" forever. One user
  logged 14 rephrase prompts in a row before giving up and phoning the desk.
- Escalations reached the ticketing system without a reason, so the desk could not tell a failed reset
  from someone who just wanted a human.

You are rebuilding three topics in the topic code editor (the YAML view in Copilot Studio). The two agent
flows they call are already built; their contract is in `agent/flows.yaml`.

## Your task

Edit the YAML under `agent/topics/`. `ConversationStart.topic.yaml` is given (it sets `Global.UserUpn`
from `System.User.PrincipalName` and initializes `Global.EscalationReason` to blank).

### Topic contract

**ResetPassword** (`OnRecognizedIntent`)
- A `modelDescription` that generative orchestration can use: what the topic does, when to use it, and
  what it does NOT handle (someone else's account, MFA/authenticator problems, changing a known password).
  At least 120 characters. At least 5 distinct `triggerQueries`.
- Ask "own account?" with a `Question` (`BooleanPrebuiltEntity`) into a Topic variable.
- Not own account: send a message that tells them their **manager** must raise a request, and end the topic.
  The reset flow must not be called and no further question asked.
- Own account: ask which system (`StringPrebuiltEntity`), call the reset flow (`InvokeFlowAction`,
  inputs `upn` = `Global.UserUpn`, `system` = the answer; output `resetStatus` into a Topic variable).
  - `"Success"`: confirm, and mention the system name (use `{Topic.YourVar}` in the message).
  - anything else: set `Global.EscalationReason` to `PasswordResetFailed` and `BeginDialog`
    `litware_itdesk.topic.Escalate`.

**Fallback** (`OnUnknownIntent`)
- Use the platform's `System.FallbackCount` (consecutive unrecognized messages). The first and second
  misses ask the user to **rephrase**; the third sets `Global.EscalationReason` to `Unrecognized` and
  begins the Escalate topic.

**Escalate** (`OnEscalate`, keep its trigger phrases)
- If `Global.EscalationReason` is blank, set it to `UserRequested`.
- Call the ticket flow with `upn`, `reason` and `summary` (`System.Activity.Text`, the user's last message);
  tell the user the ticket number from the flow output.
- Clear `Global.EscalationReason` (set it to `=Blank()`) so a later escalation is not mislabelled.

### Rules the grader enforces

- Format: Copilot Studio code-editor YAML (`kind: AdaptiveDialog`, `beginDialog`, `actions`, node `id`s).
  Formulas start with `=` and use Power Fx; anything else is a literal. `init:Topic.X` initializes a topic
  variable. Use only these node kinds: `SendActivity`, `Question`, `ConditionGroup`, `SetVariable`,
  `BeginDialog`, `InvokeFlowAction`, `EndDialog`, `EndConversation`, `CancelAllDialogs`.
- Every node and condition has an `id`, unique within its topic. Every `Question` has `prompt`, `entity`
  and a Topic `variable`. A Topic variable is never read before a node sets it. Every Global variable read
  is set somewhere. Flow inputs match `agent/flows.yaml` exactly.

The tests drive the YAML through `tests/topicsim.py`, a small simulator. It is not Copilot Studio: it
supports the node kinds above and a Power Fx subset (comparisons, `&&`/`||`/`!`, `And`/`Or`/`Not`, `&`,
`IsBlank`, `Blank`). In the real product, generative orchestration (an LLM) picks the topic from its
description; the tests pick it explicitly and check what the topic does once chosen.

## Acceptance criteria

- `make test` passes; hidden tests replay scripted conversations (success, failure, someone else's
  account, two misses then escalation, fallback counter reset after a recognized topic, two escalations in
  one session) and run the static checks above.
- The YAML would paste back into the Copilot Studio code editor (real kinds and property names).

## How to run

```
make setup   # uv sync (pyyaml, pytest)
make test    # visible tests
make clean
```

Then from the workbooks root: `/grade ms/w9-c1`. Optional: paste your topics into a Copilot Studio
trial agent's code editor and run the same conversations in the test pane with the activity map open.

## What to submit

`agent/topics/ResetPassword.topic.yaml`, `Fallback.topic.yaml`, `Escalate.topic.yaml`, and `ANSWER.md`.

## Study guide links

- [Week 9 Tue - Copilot Studio build day](../../../../microsoft-adf-powerapps-study-plan.html#week9)
- [Week 10 Mon - Design agents (topics and fallback)](../../../../microsoft-adf-powerapps-study-plan.html#week10)
- [Orchestrate agent behavior with generative AI](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-generative-actions)
- [Create and edit topics (code editor)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-create-edit-topics)
- [System topics (Fallback, Escalate, Conversation Start)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-system-topics)
- [Variables (Topic, Global, System)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-variables-about)
