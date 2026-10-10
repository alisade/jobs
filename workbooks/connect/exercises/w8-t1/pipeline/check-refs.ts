// Release pipeline gate "check-refs" (REL-412): fail the release when a promoted artifact
// references anything that does not exist in the target environment.
// Not implemented yet: the pipeline currently logs "check-refs: skipped".
import { Inventory } from "./types";

export interface RefProblem {
  artifact: string;
  /** JSONPath-like location, e.g. $.Actions[9].Parameters.LexV2Bot.AliasArn */
  path: string;
  arn: string;
  reason: "not-in-target-inventory" | "foreign-account";
}

/**
 * Every ARN in the artifact's content (any string, any depth, embedded or whole) must be either
 * the target instance ARN, or a resource in the target inventory (Lambda ARNs may carry a
 * qualifier such as :live), or belong to an explicitly allowed foreign account.
 */
export function checkRefs(artifact: string, content: string, target: Inventory, allowedAccounts: string[] = []): RefProblem[] {
  // TODO (REL-412)
  void artifact; void content; void target; void allowedAccounts;
  return [];
}
