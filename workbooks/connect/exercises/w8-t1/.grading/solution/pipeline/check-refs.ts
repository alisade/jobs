// Release pipeline gate "check-refs" (REL-412): fail the release when a promoted artifact
// references anything that does not exist in the target environment.
import { Inventory } from "./types";

export interface RefProblem {
  artifact: string;
  /** JSONPath-like location, e.g. $.Actions[9].Parameters.LexV2Bot.AliasArn */
  path: string;
  arn: string;
  reason: "not-in-target-inventory" | "foreign-account";
}

const ARN_RE = /arn:aws[a-z-]*:[a-z0-9-]+:[a-z0-9-]*:(\d{12}):[A-Za-z0-9_\-./:+=@]+/g;
const ID_KEY = /^[A-Za-z_][A-Za-z0-9_]*$/;
const child = (p: string, k: string | number) =>
  typeof k === "number" ? `${p}[${k}]` : ID_KEY.test(k) ? `${p}.${k}` : `${p}[${JSON.stringify(k)}]`;

/**
 * Every ARN in the artifact's content (any string, any depth, embedded or whole) must be either
 * the target instance ARN, or a resource in the target inventory (Lambda ARNs may carry a
 * qualifier such as :live), or belong to an explicitly allowed foreign account.
 */
export function checkRefs(artifact: string, content: string, target: Inventory, allowedAccounts: string[] = []): RefProblem[] {
  const known = new Set<string>([target.instanceArn, ...target.resources.map((r) => r.arn)]);
  const problems: RefProblem[] = [];
  const isKnown = (arn: string) => {
    if (known.has(arn)) return true;
    const m = /^(arn:aws[a-z-]*:lambda:[a-z0-9-]+:\d{12}:function:[A-Za-z0-9_-]+)(:[A-Za-z0-9_$-]+)?$/.exec(arn);
    return !!m && known.has(m[1]);
  };
  const visit = (node: unknown, path: string) => {
    if (typeof node === "string") {
      for (const m of node.matchAll(ARN_RE)) {
        const [arn, account] = m;
        if (account !== target.accountId) {
          if (!allowedAccounts.includes(account)) problems.push({ artifact, path, arn, reason: "foreign-account" });
        } else if (!isKnown(arn)) {
          problems.push({ artifact, path, arn, reason: "not-in-target-inventory" });
        }
      }
    } else if (Array.isArray(node)) {
      node.forEach((v, i) => visit(v, child(path, i)));
    } else if (node && typeof node === "object") {
      for (const [k, v] of Object.entries(node as Record<string, unknown>)) visit(v, child(path, k));
    }
  };
  visit(JSON.parse(content), "$");
  return problems;
}
