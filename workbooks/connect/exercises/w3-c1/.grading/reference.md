# Reference: connect/w3-c1

Reference handler: `.grading/solution/src/handler.ts`.

Root causes of the incident list:

| Symptom | Cause in the inherited code | Fix |
|---|---|---|
| Engineers bridged to the wrong callers | `let state` / `let employeeId` in module scope; one warm container serves concurrent calls | all state in TransactionAttributes, echoed by the service on every invocation |
| Wrong engineer at night | `onCallAt(Date.now())` evaluated when the menu digit arrives (and on a retry) | resolve from LEG-A `StartTimeInMilliseconds` |
| Silence when nobody answers | no ACTION_FAILED handling for CallAndBridge | primary -> secondary -> unavailable prompt + help desk |
| Engineer leg left open | HANGUP ignored | hang up the other leg by CallId |
| Employee IDs in logs | `console.log` of the raw id | structured log, masked id |
| Engineers ignore the call | `CallerIdNumber: legA.From` | LEG-A `To` (the hotline DID) |

Migration mapping (from the Chime SDK migration guide): SIP rule -> claimed/ported number
mapped to a flow; PlayAudioAndGetDigits -> Get customer input / Store customer input;
CallAndBridge -> Transfer to phone number; TransactionAttributes -> contact attributes;
S3 WAV -> prompt library or TTS; HANGUP handling -> disconnect flow. The Avaya `X-Employee-Id`
header has no documented equivalent on a PSTN transfer into Connect, so during coexistence use
a data dip (DynamoDB keyed on ANI + DNIS + short TTL written by the Avaya side, or an API call)
and drop it once the help desk itself is on Connect. Port the hotline number from the Chime SDK
to Connect by support case (2-4 weeks); test the flow on a temporary claimed number first.
