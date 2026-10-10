# connect/w3-c2 - Voice Connector as code for the Avaya coexistence trunk

**Type:** coding | **Estimate:** 1.5-2 hours | **Study plan:** Week 3 (Thu: Chime SDK Voice Connector; Tue: BYOC and what Connect does not do)

## Scenario

During the 18-month coexistence period LFG keeps its Avaya Aura estate for back-office
users. Its carrier contract ends in March, so the Avaya SBCE pair in Ashburn (and the DR SBCE
in Dallas) will trunk to the PSTN through Amazon Chime SDK Voice Connector: SIP trunking for a
PBX/SBC, which is exactly what Voice Connector is for. (Bridging that trunk into Connect is a
different matter: AWS does not support routing a separate provider into Connect through a
Voice Connector without an architecture review. The help desk numbers are ported to Connect
instead; this trunk only serves the Avaya side.)

The 2025 proof of concept left a CDK stack that the security review rejected and the network
team cannot operate. CloudFormation has no resource types for Chime SDK Voice, so the stack
uses custom resources that call the `chime-sdk-voice` API (service `ChimeSDKVoice`, IAM
prefix `chime`). Your job is to make it production-grade. Synth runs offline in the tests;
nothing is deployed.

Review findings you must close:

1. Encryption is off. Security policy requires TLS signaling and SRTP media on every trunk.
2. The termination allow list includes the internal `10.20.0.0/16` range (copied from the
   SBC's LAN side). Voice Connector only accepts publicly routable addresses; a bad entry
   should fail at synth time, not at 2 AM.
3. CPS is hard-coded to 1 (the default quota); prod is approved for 20.
4. Origination sends UDP 5060 with every route at priority 1, weight 1: no TLS and no
   distinction between the Ashburn pair (50/50) and the Dallas DR SBC (priority 2).
5. Nobody can troubleshoot: SIP message logs and media metric logs (jitter, packet loss, MOS)
   are off.
6. The termination password sits in `config/environments.json` and lands in the template as
   a custom resource parameter. It must come from Secrets Manager at deploy time.
7. Only one Voice Connector, in us-east-1. The design calls for one per Region (us-east-1,
   us-west-2) behind a Voice Connector group (priority 1 and 2) for inbound failover.
8. Configuration changes never apply: the Put* calls only run on create.

## Requirements

- Per entry in `voiceConnectors`: `CreateVoiceConnector` (`AwsRegion`, `RequireEncryption:
  true`, name `<namePrefix>-<key>`, tags from config), physical id from the response,
  `DeleteVoiceConnector` on delete; `PutVoiceConnectorTermination`,
  `PutVoiceConnectorOrigination` (TCP 5061, priority/weight from config),
  `PutVoiceConnectorLoggingConfiguration` (both logs on), each on create and update.
- Synth throws a clear error for any private (RFC 1918, CGNAT, loopback, link-local)
  termination CIDR or origination host. Fix the config too.
- Termination credentials: a custom resource backed by your own provider Lambda that reads
  the secret (`secretArn`, JSON key `password`) at deploy time and calls
  `PutVoiceConnectorTerminationCredentials`. The template carries only the secret ARN. The
  function may read only that secret. It runs after the termination settings exist.
- `CreateVoiceConnectorGroup` with both Voice Connectors (priority from config), deleted on
  stack delete.
- Outputs: each Voice Connector id and outbound host name (for the SBC trunk config).

## Acceptance criteria (what the grader checks)

- Decoded SDK calls in the synthesized template match the requirements (Regions, names,
  tags, encryption, termination, origination routes, logging, update behaviour, group).
- No plaintext password anywhere in the template; no `PutVoiceConnectorTerminationCredentials`
  SDK-call parameter; the secret-read permission is scoped to the secret.
- Private addresses are rejected at synth.
- `ANSWER.md` covers why each finding mattered and what you would still do before go-live.

## How to run

```bash
make setup     # links the shared toolchain
make test      # synthesizes offline and checks the template
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w3-c2
make clean
```

`tests/template.ts` shows how the tests decode `Custom::AWS` resources; use it to inspect
your own template. Parameter names follow the `@aws-sdk/client-chime-sdk-voice` types
(`node_modules/@aws-sdk/client-chime-sdk-voice/dist-types/models/models_0.d.ts`).
Terraform users: the AWS provider has `aws_chime_voice_connector*` resources for the same job.
