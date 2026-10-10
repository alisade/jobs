import { normalize } from "./analysis";
import { ComplianceResult, CompliancePolicy, ContactAnalysis, Finding, Turn } from "./types";

const hit = (turn: Turn, phrases: string[]) => {
  const text = normalize(turn.Content);
  return phrases.some((p) => text.includes(normalize(p)));
};

/** Evaluate one contact against the help desk compliance policy. */
export function evaluateCompliance(a: ContactAnalysis, policy: CompliancePolicy): ComplianceResult {
  const turns = [...a.file.Transcript].sort((x, y) => x.BeginOffsetMillis - y.BeginOffsetMillis);
  const agent = turns.filter((t) => t.ParticipantId === "AGENT");
  const findings: Finding[] = [];

  const greetingOk = agent.some((t) => t.BeginOffsetMillis <= policy.greeting.withinMillis && hit(t, policy.greeting.phrases));
  const closingOk = agent.slice(-policy.closing.lastAgentTurns).some((t) => hit(t, policy.closing.phrases));
  const disclosureOk = agent.some((t) => hit(t, policy.requiredDisclosure.phrases));
  if (!disclosureOk) {
    findings.push({ contactId: a.contactId, ruleId: policy.requiredDisclosure.ruleId, priority: policy.requiredDisclosure.priority, turnIds: [], atMillis: null });
  }
  for (const rule of [policy.escalationLanguage, policy.prohibitedAgentLanguage]) {
    const ev = turns.filter((t) => t.ParticipantId === rule.participant && hit(t, rule.phrases));
    if (ev.length) findings.push({ contactId: a.contactId, ruleId: rule.ruleId, priority: rule.priority, turnIds: ev.map((t) => t.Id), atMillis: ev[0].BeginOffsetMillis });
  }
  findings.sort((x, y) => x.priority - y.priority || x.ruleId.localeCompare(y.ruleId));
  return {
    contactId: a.contactId,
    greetingOk,
    closingOk,
    disclosureOk,
    adherent: greetingOk && closingOk,
    escalation: findings.some((f) => f.ruleId === policy.escalationLanguage.ruleId),
    prohibited: findings.some((f) => f.ruleId === policy.prohibitedAgentLanguage.ruleId),
    findings,
  };
}
