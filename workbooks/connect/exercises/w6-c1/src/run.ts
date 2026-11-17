import { loadBatch, Batch } from "./analysis";
import { evaluateCompliance } from "./compliance";
import { agentKpis } from "./kpi";
import { QaTaskClient } from "./servicenow";
import { AgentKpi, ComplianceResult, CompliancePolicy, ContactRecord, Finding } from "./types";

export interface BatchReport {
  processed: number;
  rejected: Batch["rejected"];
  results: ComplianceResult[];
  agents: AgentKpi[];
  tasks: { correlationId: string; number: string; created: boolean; priority: number }[];
  taskErrors: { correlationId: string; message: string }[];
}

const RULE_TITLES: Record<string, string> = {};

function describe(f: Finding, rec: ContactRecord | undefined, policy: CompliancePolicy): { short: string; long: string } {
  const who = rec ? `${rec.agentName} (${rec.agentId}), queue ${rec.queue}` : "unknown agent";
  const title = RULE_TITLES[f.ruleId] || f.ruleId;
  const where = f.atMillis === null ? "phrase not found in any agent turn" : `first evidence at ${Math.round(f.atMillis / 1000)} s, turns ${f.turnIds.join(", ")}`;
  return {
    short: `QA review: ${title} on contact ${f.contactId}`,
    // Never copy transcript text into ServiceNow: point reviewers at the contact instead.
    long: `Rule ${f.ruleId} (policy ${policy.policyVersion}) flagged contact ${f.contactId}. Agent: ${who}. Evidence: ${where}. Review the redacted transcript in Contact details.`,
  };
}

/**
 * TODO: load the batch, evaluate every accepted analysis, compute agent KPIs and raise one QA
 * task per (contact, rule) finding with correlation id `${contactId}:${ruleId}`, using
 * describe() for the text. A failure on one task goes to taskErrors; the batch continues.
 */
export async function processBatch(opts: {
  dir: string;
  policy: CompliancePolicy;
  contacts: Record<string, ContactRecord>;
  sn: QaTaskClient;
}): Promise<BatchReport> {
  void [loadBatch, evaluateCompliance, agentKpis, describe];
  throw new Error(`TODO: processBatch ${opts.dir}`);
}
