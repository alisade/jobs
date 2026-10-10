# Reference: connect/w3-c2

Reference stack: `.grading/solution/lib/voice-connector-stack.ts`; fixed config in
`.grading/solution/config/environments.json` (10.20.0.0/16 and legacyPassword removed).

Design points:

- A `TrunkVoiceConnector` construct per Region: CreateVoiceConnector (RequireEncryption,
  AwsRegion, tags; physical id from `VoiceConnector.VoiceConnectorId`; DeleteVoiceConnector on
  delete), then PutVoiceConnectorTermination / Origination / LoggingConfiguration with the same
  call on create and update and a stable physical id (so an update re-applies, never replaces).
- Validation: private IPv4 (10/8, 172.16/12, 192.168/16, 100.64/10, 127/8, 169.254/16) in the
  termination allow list or origination hosts throws at synth with the offending values.
- Credentials: a `Custom::VoiceConnectorTerminationCredentials` resource on a `Provider`
  whose handler reads the secret and calls PutVoiceConnectorTerminationCredentials;
  `secret.grantRead(fn)` scopes GetSecretValue to the secret ARN. It depends on the
  termination resource. AwsCustomResource parameters are stored in the template in clear
  text, which is why the password cannot go through it. For rotation, add the secret's
  version (or a hash) as a property so a new version triggers an update.
- Group: CreateVoiceConnectorGroup / UpdateVoiceConnectorGroup / DeleteVoiceConnectorGroup with
  us-east-1 at priority 1 and us-west-2 at priority 2. Groups fail over inbound calls between
  Voice Connectors (and Regions); origination routes pick an SBC within one Voice Connector.
- Origination over TLS uses TCP port 5061; encryption also forces SRTP (SDES keys) and blocks
  unencrypted outbound calls.

Talking points: Terraform has native `aws_chime_voice_connector*` resources, which avoids
custom-resource drift blind spots; whichever tool, alarms on `AWS/ChimeVoiceConnector`
(Throttles, Sip4xx/5xx codes, MOS, jitter, packet loss) and the SBC's TLS trust store (Amazon
Trust Services + Starfield roots; Voice Connector does not do mutual TLS; DHE and non-GCM
suites stopped working on 2026-08-01).
