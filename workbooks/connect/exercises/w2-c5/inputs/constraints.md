# Constraints for the IVR redesign

- Target platform: Amazon Connect flows + Lex V2 (en_US, es_US); Okta Verify push for verification
  (Okta APIs available); ServiceNow Table API for ticket status; HR directory export with phone numbers.
- Every prompt must be recordable by the existing voice talent or Amazon Polly neural voices.
- Legal requires the recording notice. HR forbids reading back personal data.
- Accessibility: TTY/relay callers must be able to reach an agent; DTMF must remain available.
- Success targets from the program: containment 30% on password reset/unlock and VPN how-to, average
  time to agent under 60 s for non-contained calls, zero-out under 3%.
