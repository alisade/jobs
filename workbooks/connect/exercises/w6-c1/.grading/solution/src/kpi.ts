import { AgentKpi, ComplianceResult, ContactAnalysis, ContactRecord } from "./types";

const r2 = (n: number) => Math.round(n * 100) / 100;
const mean = (xs: number[]) => (xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : 0);

/** Per-agent sentiment and compliance KPIs. Contacts without a contact record are ignored. */
export function agentKpis(analyses: ContactAnalysis[], results: ComplianceResult[], contacts: Record<string, ContactRecord>): AgentKpi[] {
  const byContact = new Map(results.map((r) => [r.contactId, r]));
  const groups = new Map<string, { rec: ContactRecord; items: { a: ContactAnalysis; r: ComplianceResult }[] }>();
  for (const a of analyses) {
    const rec = contacts[a.contactId];
    const r = byContact.get(a.contactId);
    if (!rec || !r) continue;
    const g = groups.get(rec.agentId) || { rec, items: [] };
    g.items.push({ a, r });
    groups.set(rec.agentId, g);
  }
  const out: AgentKpi[] = [];
  for (const [agentId, g] of groups) {
    const n = g.items.length;
    const cc = g.items.map((x) => x.a.file.ConversationCharacteristics);
    const deltas = cc
      .map((c) => c.Sentiment?.SentimentByPeriod?.QUARTER?.CUSTOMER || [])
      .filter((q) => q.length >= 2)
      .map((q) => q[q.length - 1].Score - q[0].Score);
    let agentTalk = 0;
    let totalTalk = 0;
    for (const c of cc) {
      if (!c.TalkTime) continue;
      agentTalk += c.TalkTime.DetailsByParticipant.AGENT?.TotalTimeMillis || 0;
      totalTalk += c.TalkTime.TotalTimeMillis;
    }
    out.push({
      agentId,
      agentName: g.rec.agentName,
      contacts: n,
      avgCustomerSentiment: r2(mean(cc.map((c) => c.Sentiment?.OverallSentiment.CUSTOMER ?? 0))),
      avgCustomerSentimentDelta: r2(mean(deltas)),
      agentTalkRatio: totalTalk > 0 ? r2(agentTalk / totalTalk) : null,
      agentInterruptionsPerContact: r2(mean(cc.map((c) => (c.Interruptions?.InterruptionsByInterrupter.AGENT || []).length))),
      adherenceRate: r2(g.items.filter((x) => x.r.adherent).length / n),
      disclosureRate: r2(g.items.filter((x) => x.r.disclosureOk).length / n),
      escalations: g.items.filter((x) => x.r.escalation).length,
      prohibited: g.items.filter((x) => x.r.prohibited).length,
    });
  }
  return out.sort((x, y) => x.agentId.localeCompare(y.agentId));
}
