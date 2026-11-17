# Reference: ms/w10-t1

Injected fault: `SubmitLeaveRequest.tool.yaml` was cloned from the balance tool. Its description is
identical ("Handles leave and PTO for employees.") and its display name is the generic "Leave and PTO".
The balance tool's only input has no description. The Submit tool's input descriptions use balance
language ("vacation days ... asking about", "how many ... days of leave are left"). With generative
orchestration, descriptions are the most important selection signal, then names and input names and
descriptions (Learn: Orchestrate agent behavior with generative AI). Identical descriptions make the
choice unpredictable; the input text tips it to Submit.

Red herring: Facilities knowledge indexing warnings (FileTooLarge for 3 files) every night; unrelated.

Reference fix: `.grading/solution/agent/tools/*.tool.yaml`. Key properties:
- unique, specific names ("Get time off balance" vs "Submit time off request");
- one or two sentences of what and when, plus what it does not do (Learn recommends stating what a
  similar tool cannot do);
- input descriptions that explain how to fill them (from the user's profile vs ask the user).

What a strong answer adds:
- The eval run happened after the import: move agent evaluation (Copilot Studio test sets) into the
  pipeline as a pre-deployment gate.
- Monitoring: Copilot Studio analytics (tool usage, abandonment, session outcomes, CSAT) and
  Application Insights telemetry per release, with alerts.
- Safety: a write tool must confirm before acting (instructions plus the tool's confirmation), so a
  misroute degrades to a wrong question, never a wrong booking.

Interview angles:
- Why did the old agent work before 1.8? (Only one leave tool; nothing to confuse.)
- How do you test non-deterministic routing? (Scored test sets run several times, pass-rate thresholds,
  not single exact-match runs.)
