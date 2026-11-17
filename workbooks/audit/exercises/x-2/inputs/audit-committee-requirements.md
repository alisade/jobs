# MFH audit committee: conditions for using ControlPilot in the FY2026 SOX cycle

Minutes extract, audit committee meeting 2026-11-04 (fictional).

1. ControlPilot may perform testing steps; it may not sign off. Every exception, every
   "not evaluable" item and a random 10% of passes are reviewed by a human who did not prepare
   the work. Reviewer and preparer identities are recorded.
2. Every conclusion in a workpaper must cite the evidence it rests on (document, page or cell).
   The external auditor must be able to re-perform a sample item from the workpaper alone.
3. Evidence and workpapers are retained 7 years and must not be modifiable after sign-off.
4. The committee wants quarterly metrics per control: accuracy and exception recall against a
   human-labeled set, consistency, cost, and the number of human overrides.
5. ControlPilot is itself an in-scope application: changes to its code, prompts, model version and
   tool permissions follow the CM-03 program-change control (ticket, independent approval, tests).
6. No client or employee data leaves the approved regions (US). No long-lived credentials.
7. A kill switch: internal audit can stop all agent activity within 15 minutes.
