# ANSWER: connect/w3-c2 Voice Connector as code

## Approach

Decoded the PoC template with tests/template.ts, mapped each review finding to an SDK call,
and checked parameter names against the chime-sdk-voice SDK types.

## Fix

TrunkVoiceConnector construct per Region (encrypted, tagged, delete on teardown); termination
with public /32s, US/CA, CPS 20; origination TLS/TCP 5061 with the Ashburn pair at priority 1
50/50 and Dallas at priority 2; both log types; every Put* on create and update. Synth-time
private-address validation, and the config fixed. Credentials via a provider Lambda reading the
secret (grantRead scoped to the ARN), after termination. Voice Connector group with us-east-1
priority 1, us-west-2 priority 2. Outputs for VC ids and outbound host names. make test passes.

## Trade-offs / what I would do in production

Custom resources hide drift; Terraform's aws_chime_voice_connector* resources would be simpler
if the team runs Terraform. Rotation: pass the secret version as a property. Before cutover:
SBC trust store with ATS/Starfield roots and GCM suites, OPTIONS pings visible, test calls per
route, alarms on Throttles, Sip5xxCodes and MOS. This trunk serves Avaya only; help desk numbers
port to Connect (no supported VC-into-Connect bridging without AWS review).
