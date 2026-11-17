# Reference: ms/w9-c1

Reference topics: `.grading/solution/agent/topics/*.topic.yaml`.

Why it is built this way:

1. **Generative orchestration reads descriptions.** With generative orchestration on, topics are selected
   by their description (the trigger node shows "The agent chooses"); trigger phrases matter for classic
   orchestration. A description that says what the topic does NOT handle reduces overlap with other
   topics and tools (Learn: "It can also help to indicate what they can't do").
2. **Gate before side effects.** Ask ownership first and put the reset flow only inside the true branch.
   The else branch of the status check escalates, so an unexpected status fails safe.
3. **System.FallbackCount.** The default Fallback system topic uses `=System.FallbackCount < 3` to decide
   between "rephrase" and escalation. It counts consecutive unrecognized messages and resets when a topic
   is recognized, so you do not need your own counter.
4. **Global variables carry cross-topic context** (here: why we escalate). Default it in the receiver and
   clear it after use, or the next escalation inherits a stale reason.
5. **Topic outputs vs messages.** In generative mode, topics can return outputs for the orchestrator to
   phrase; here explicit messages are fine because the flow results are user-facing confirmations.

Interview angles:
- Where must the "own account only" rule be enforced so it cannot be bypassed? (In the flow / identity
  system; the topic is UX.)
- How would you detect that fallback loops are hurting users? (Analytics: escalation and abandonment
  rates, unrecognized-utterance themes; then add topics or knowledge.)
- What changes when you move this agent from dev to prod? (Solution, connection references, environment
  variables for flow endpoints, authentication settings per environment.)
