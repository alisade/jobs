# Rubric: connect/w3-c2 Voice Connector as code for the Avaya coexistence trunk
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Secret handling | 15 | Full: password only in Secrets Manager, provider Lambda reads it at deploy time, template carries only the ARN, read permission scoped to that secret, legacy password removed from config; ANSWER.md mentions rotation (re-run on secret version change, e.g. pass the version id or a hash as a property) and that AwsCustomResource parameters are stored in the template and visible to anyone with cloudformation:GetTemplate. Partial: secret used but via a dynamic reference or an over-broad policy. Zero: still plaintext. |
| 3 | Telephony correctness | 10 | Full: TLS on TCP 5061 with SRTP, priority 1 pair at 50/50 and DR at priority 2, group priorities by Region, explains how origination priority/weight differs from group failover (routes pick an SBC for a VC; the group picks a VC across Regions for inbound numbers). Partial: right values, no explanation. |
| 4 | Operability | 10 | Full: SIP + media metric logs (names the log groups /aws/ChimeVoiceConnectorSipMessages/<id> and /aws/ChimeVoiceConnectorLogs/<id>), outputs for the SBC team, update semantics on every Put*, synth-time validation with a useful message. |
| 5 | Code quality | 5 | One construct per trunk, no copy-paste per Region, typed config, no dead code. |
| 6 | ANSWER.md trade-offs | 10 | Full: at least three of: custom resources vs Terraform aws_chime_voice_connector* (drift, imports), CPS and concurrent-call quotas, SBC trust store (Amazon Trust Services and Starfield roots, no mutual TLS, cipher deprecations), alarms on AWS/ChimeVoiceConnector metrics (Throttles, Sip5xxCodes, MOSBetweenVcAndCustomer), the unsupported VC-into-Connect pattern and why numbers are ported to Connect instead. Partial: generic. |
Total: 100
