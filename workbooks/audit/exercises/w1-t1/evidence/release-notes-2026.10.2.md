# ControlPilot release 2026.10.2 (deployed 2026-10-06)

- DEV-2287 Prompt v2 for CM-03: clearer key names for the attribute flags, adds a one-line summary
  per sample for the workpaper. Reviewed by the audit innovation lead.
- DEV-2291 Temperature 0.0 -> 0.4 for more natural summaries.
- DEV-2293 Moved from gemini-3.6-flash to gemini-3.8-flash (same pricing tier).
- DEV-2295 Contract hardening: ChangeAssessment ignores unknown keys so that prompt tweaks never
  break a production run (we lost a night in September to a ValidationError on a new key).
