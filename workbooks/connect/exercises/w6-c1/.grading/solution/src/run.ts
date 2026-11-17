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

/** Load, evaluate, aggregate and raise one QA task per (contact, rule) finding. */
export async function processBatch(opts: {
  dir: string;
  policy: CompliancePolicy;
  contacts: Record<string, ContactRecord>;
  sn: QaTaskClient;
}): Promise<BatchReport> {
  const batch = loadBatch(opts.dir);
  const results = batch.analyses.map((a) => evaluateCompliance(a, opts.policy));
  const agents = agentKpis(batch.analyses, results, opts.contacts);
  const tasks: BatchReport["tasks"] = [];
  const taskErrors: BatchReport["taskErrors"] = [];
  for (const r of results) {
    for (const f of r.findings) {
      const correlationId = `${f.contactId}:${f.ruleId}`;
      const d = describe(f, opts.contacts[f.contactId], opts.policy);
      try {
        const t = await opts.sn.ensureTask({ correlationId, shortDescription: d.short, description: d.long, priority: f.priority, assignmentGroup: opts.policy.qaAssignmentGroup });
        tasks.push({ correlationId, number: t.number, created: t.created, priority: f.priority });
      } catch (err) {
        taskErrors.push({ correlationId, message: (err as Error).message });
      }
    }
  }
  return { processed: batch.analyses.length, rejected: batch.rejected, results, agents, tasks, taskErrors };
}
