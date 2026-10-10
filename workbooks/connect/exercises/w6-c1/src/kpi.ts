import { AgentKpi, ComplianceResult, ContactAnalysis, ContactRecord } from "./types";

/**
 * Per-agent sentiment and compliance KPIs (see the AgentKpi field comments in types.ts).
 * Contacts without a contact record are ignored. Rows sorted by agentId.
 */
export function agentKpis(analyses: ContactAnalysis[], results: ComplianceResult[], contacts: Record<string, ContactRecord>): AgentKpi[] {
  throw new Error(`TODO: agentKpis over ${analyses.length} analyses, ${results.length} results, ${Object.keys(contacts).length} contacts`);
}
