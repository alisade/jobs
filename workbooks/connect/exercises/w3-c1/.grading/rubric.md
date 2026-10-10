# Rubric: connect/w3-c1 Keep the on-call hotline alive: PSTN audio handler
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | State and concurrency model | 15 | Full: no module-level mutable call state; TransactionAttributes as the only state, string values, minimal keys; explains warm-container reuse across concurrent calls and the 5 s retry / 20 s hang-up behaviour (handler must be deterministic and fast, no side effects that double on retry). Partial: fixed but cannot explain why the old code cross-wired calls. Zero: state in a Map keyed by TransactionId in module scope (still breaks across containers). |
| 3 | Call-leg handling | 10 | Full: hangs up the remaining leg by CallId, handles both HANGUP directions, input failures and INVALID_LAMBDA_RESPONSE; never returns actions on a disconnected leg. Partial: one direction only. |
| 4 | Telephony judgement | 10 | Full: hotline DID as caller ID (engineers recognise it; explains reputation/STIR-SHAKEN attestation concerns of presenting a number you do not own), header validated before trust, time zone from call start. Partial: right code, no reasoning. |
| 5 | Logging and data handling | 5 | One structured line per invocation, masked employee ID, no raw SIP headers or caller numbers in logs. |
| 6 | Migration mapping in ANSWER.md | 10 | Full: maps SIP rule -> phone number/flow, PlayAudioAndGetDigits -> Get/Store customer input, CallAndBridge -> Transfer to phone number (or queue/quick connect for engineers), TransactionAttributes -> contact attributes, S3 prompts -> prompt library; notes that X- headers from the Avaya SBC do not reach Connect over the PSTN, so context needs another path (data dip keyed on ANI/DNIS/time, or an API/CTI correlation); mentions porting the hotline number from Chime SDK to Connect by support case. Partial: generic "move to Connect". |
Total: 100
