# LFG service desk QA: current state (input for the design)

Source: QA lead interview (Mei Tanaka), 2026-10-02, and the Avaya-era QA workbook.

## Volumes and people
- Contacts per month after migration: 62,000 voice, 18,000 chat, 4,000 email (email from Q1 2027).
- Agents: 140 (Charlotte 40, Pune 70 offshore vendor, Monterrey 30 nearshore vendor), 14 team leads.
- QA analysts: 3 (Charlotte). Today they hand-score 2% of voice calls on a 22-question spreadsheet,
  about 1,200 evaluations a month, 25 minutes each. Chat is not reviewed. Vendor QA in Pune scores
  its own agents on a different form; scores are 9 points higher than LFG's on the same calls.
- Calibration: none since 2025. Agents dispute 15% of evaluations; disputes take 2 weeks.

## Requirements and drivers
- PCI DSS: agents must never take card data on the help desk; if a caller reads card digits the
  agent must stop them. SOX: access requests to finance systems need manager approval recorded.
- Security policy: agents must never ask for a password or MFA code; disclosure "Larkspur IT will
  never ask for your password" on every password/MFA contact.
- HR: coaching feedback within 5 business days; vendor contracts pay a quality bonus on a QA score
  above 85 (so the score must be defensible and comparable across sites).
- Works council (Monterrey) and India vendor contract: agents must be told how monitoring works.
- Executive ask (CIO): "every contact checked for the things that can hurt us, humans only where it
  matters", and a monthly QA trend in the service review.

## Platform facts (Amazon Connect Customer, us-east-1, DR us-west-2)
- Conversational analytics (formerly Contact Lens) enabled in flows for voice and chat, redaction on,
  RedactedAndOriginal for legal hold (originals restricted to the legal role).
- ServiceNow is the system of record for incidents and for HR coaching tasks.
- Languages: English; Spanish for Monterrey chat pilot.
