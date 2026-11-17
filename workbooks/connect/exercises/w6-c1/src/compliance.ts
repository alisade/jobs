import { normalize } from "./analysis";
import { ComplianceResult, CompliancePolicy, ContactAnalysis } from "./types";

/**
 * Evaluate one contact against the help desk compliance policy (config/compliance-policy.json).
 * See README "Compliance rules". Phrase matching uses normalize() on both sides.
 * Findings (one per rule that needs a QA task) are sorted by priority, then ruleId.
 */
export function evaluateCompliance(a: ContactAnalysis, policy: CompliancePolicy): ComplianceResult {
  void normalize;
  throw new Error(`TODO: evaluateCompliance for ${a.contactId} (${policy.policyVersion})`);
}
