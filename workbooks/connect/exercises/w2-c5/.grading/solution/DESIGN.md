# LFG Service Desk IVR and self-service journey redesign

Author: Lead Amazon Connect architect        Version: 1.0

## 1. Goals and success metrics

| Metric | Definition | Today | Target |
|---|---|---|---|
| Containment (password reset/unlock, VPN how-to) | contacts that end in self-service with a success outcome AND no contact by the same employee about the same driver within 7 days / all contacts of those drivers | ~0% | 30% |
| Time to agent | seconds from call start to queue entry, non-contained calls | ~94 s (14 + 22 + 38 + ~20) | < 60 s |
| Zero-out | callers pressing 0 or asking for an agent before stating a need | 6.8% at main menu | < 3% |
| IVR hang-up | hang-ups before routing (excluding contained) | ~9% cumulative | < 4% |
| Misroute | transfers after answer | 4-22% by path (apps 22%) | < 5% |
| CSAT (phone) | post-contact survey | 3.9 | 4.3 |

Containment is only real if the employee does not come back: every self-service outcome is checked
against 7-day repeat contacts.

## 2. Diagnosis of the current IVR

- Callers spend ~94 s in the IVR before queueing: ~37,000 caller-minutes a month of navigation.
- Language menu first (14 s) although 92% choose English and the HR directory knows the language.
- Employee ID entry (22 s) fails on the first try for 31% and never succeeds for 9% (~2,100 calls a
  month), and the ID is not passed to the agent, so agents ask again (verbatim 1). Identity work is
  done twice and helps nobody.
- Main menu: 7 options, 31 s; 9% repeat, 6.8% zero-out. Six of seven branches go to the same
  general skill: the menu sorts nothing it uses.
- Password: 22% of calls; the IVR tells locked-out callers to "reset online", which they cannot do
  (verbatim 3). MFA/Okta Verify is buried (21% of that sub-menu).
- Ticket status (6%) has no self-service at all.
- Apps: Workday calls land with SAP agents (22% transferred after answer).
- Queue: no wait time, no callback; after hours dead-ends with no outage path; relay callers time out.

## 3. Design principles

1. Identify silently (ANI, language preference) before asking anything.
2. Ask once, use everywhere: whatever the caller says or enters is passed to the bot, the agent and
   ServiceNow.
3. Lead with the most frequent needs; offer self-service only where it can finish the job.
4. One open question with natural language, with a short DTMF safety net; never more than 4 options.
5. No dead ends: every failure path ends at an agent (or a callback), never "Goodbye".
6. Short prompts: under 8 s each; the recording notice once.
7. Accessible by default: DTMF everywhere, longer timeouts on request, relay-friendly.

## 4. Target journey map

```text
call --> [identify: ANI -> HR directory (DynamoDB, < 100 ms)]
          |-- found: name, language, VIP flag, open incidents count
          |-- not found: continue as unidentified
     --> [major-incident check: active outage message + SMS status link]  (only when flag on)
     --> [greeting in preferred language + recording notice, 7 s]
     --> VIP? ------------------------------------------------------------> VIPDesk (priority 1)
     --> [open incidents? "Are you calling about ticket INC... ?" yes -> status read-out / agent with incident]
     --> [Lex: "In a few words, what do you need help with?"  (DTMF: 1 password or Okta, 2 something else)]
          |-- ResetPassword / UnlockAccount --> verify (Okta Verify push) --> reset or unlock --> SMS link --> done
          |                                       \-- push fails/declined --> PasswordReset queue (context)
          |-- MfaEnroll ----------> SMS enrollment guide + offer agent ----------> PasswordReset queue
          |-- VpnHelp (QnA) ------> answer from KB article + "did that fix it?" -> done / GeneralSupport
          |-- TicketStatus -------> ServiceNow lookup -> read status -> done / agent
          |-- SAP / Workday / Salesforce --> Applications with routing criteria (Workday-trained first)
          |-- hardware / software / other -> GeneralSupport (driver attribute set)
          |-- TalkToAgent or 2 no-matches --> best-guess queue from what was said, else GeneralSupport
     --> queue: position-free wait message; callback offer when the oldest contact > 180 s
chat (portal widget): SSO context (employee ID, language) -> same Lex bot -> same queues and context
```

## 5. Identification and authentication tiers

| Tier | Mechanism | Unlocks | On failure |
|---|---|---|---|
| T0 identified | ANI matches exactly one employee phone in the HR directory; chat: portal SSO token | screen pop, ticket status, how-to, routing by language/VIP | unidentified: ask employee ID once (DTMF or spoken), 2 tries, then continue to an agent |
| T1 verified | T0 + Okta Verify push approved within 30 s (Lambda async mode + Wait block) | password reset/unlock, MFA guidance | push timeout/decline -> agent with verification=failed |
| T2 step-up | agent-initiated (e.g. CLEAR verification link) | admin accounts, MFA factor reset | agent-only |

Knowledge questions (DOB, SSN last 4) are removed; Voice ID is not an option (end of support 2026-05-20).

## 6. Natural language vs DTMF

- One open question via Lex (en_US, es_US) with the intents in section 4; AMAZON.QnAIntent answers VPN
  and how-to questions from the knowledge base; assisted slot resolution for application names and
  device types.
- DTMF safety net in the same prompt: "or press 1 for passwords and Okta, 2 for anything else".
- Confidence: below the bot threshold -> one reprompt with examples ("for example: unlock my account,
  VPN won't connect"); second miss -> route to GeneralSupport with the transcript, never a third try.
- Disambiguation when two intents are close ("Is this about SAP or Workday?").
- No-input: one reprompt, then DTMF menu, then agent. Barge-in enabled on every prompt.

## 7. Containment and deflection by driver

| Driver (share) | Self-service | Expected containment | Deflection | Context to agent on failure |
|---|---|---|---|---|
| Password reset/unlock (~16%) | push verify -> reset/unlock -> SMS link | 40-50% of identified callers (ANI hit rate ~85%, push enrollment ~75%) | SSPR campaign in portal | verification result, step reached |
| MFA / Okta Verify (~5%) | SMS enrollment guide | 15% | portal enrollment page | device type |
| VPN how-to (~8%) | QnAIntent answer + confirmation | 25% | chat with same answers | article shown, caller said not fixed |
| Ticket status (6%) | ServiceNow read-out | 60% | portal and SMS updates | incident number |
| Others | none (routing only) | 0% | chat for software requests | driver, transcript |

Weighted: (16% x 45%) + (8% x 25%) = ~9% of all calls, i.e. ~38% of the password/unlock and VPN demand,
which leaves margin over the program's 30% target for estimate error. These are estimates to validate in
the pilot, not promises.

## 8. Queue experience: callbacks and queue-in-place

- Wait message every 60 s; no "your call is important".
- Callback offer when Get queue metrics shows the oldest contact > 180 s: queued callback keeps the
  caller's place, confirmed by SMS; VIP never offered callbacks (always priority 1).
- Major-incident mode: outage message first, SMS status link, option to stay for an agent.
- After hours: portal reset reminder, "press 9 to report an outage" to the 24x7 line, never a bare goodbye.

## 9. Prompts (sample script)

| Step | Today | New |
|---|---|---|
| Greeting | "Thank you for calling ... menu options have changed ... For English press 1 ..." (14 s) | "Hi Maria, LFG IT. This call may be recorded." (4 s) |
| Ask | 7-option main menu (31 s) | "In a few words, what do you need help with? Or press 1 for passwords and Okta, 2 for anything else." (7 s) |
| Self-service | "reset at reset.lfg.example" | "I've sent an Okta Verify request to your phone. Approve it and I'll unlock your account." |
| Done | - | "Your account is unlocked. I've texted you a reset link. Anything else?" |
| Handoff | "Please hold for the next available agent." | "I'll connect you to the password team and tell them what we tried." |

## 10. Accessibility and languages

- Language from the directory (or the last chat); "para espanol diga espanol u oprima 9" once in the greeting.
- DTMF works at every step; "press star to hear that again"; option to extend timeouts (relay users).
- Relay/TTY callers: on two no-inputs route straight to an agent with relay=true.
- Chat widget meets WCAG 2.2 AA; same bot, same answers.

## 11. Measurement and experimentation

- Contact attributes at every step: idMethod, verification, intent, botConfidenceBand, selfServiceOutcome,
  handoffReason; flow logs on; contact records to the data lake.
- Dashboards: containment by intent with the 7-day repeat check, time to agent, zero-out, misroutes.
- Rollout: pilot on a new DID for Pune agents' callers (10%), then A/B by routing 50% of the main number
  through the new flow (distribute by percentage) for two weeks; go/no-go on containment, CSAT, repeats.

## 12. Implementation notes in Amazon Connect

- Flows: Inbound main flow with flow modules for identify, major-incident check, verify, handoff;
  customer queue flow with wait messages and callback offer.
- Lex V2 bot with the intents above; session attributes in (employeeId, language) and out (intent,
  slots, outcome); Connect passes them to the agent via contact attributes.
- Lambdas: identify (< 1 s budget, synchronous), Okta push (async mode, up to 60 s with Wait), ServiceNow
  ticket lookup (2 s), all with error branches to the agent path.
- Agent gets a screen pop in ServiceNow with intent, verification result and bot transcript summary.
- Tests before go-live: flow lint and simulation in CI, Connect flow tests for each path, 200 scripted
  test calls (both languages, DTMF and voice), relay test, load test at 2x peak.

## 13. Risks and open questions

- ANI hit rate unknown for vendor softphones and mobile numbers: measure in the first week.
- Okta Verify enrollment at 75% is an assumption: the Okta admin to confirm; non-enrolled go to agents.
- Spanish bot accuracy: Monterrey agents to provide 300 sample utterances.
- Legal review of the shortened recording notice.
