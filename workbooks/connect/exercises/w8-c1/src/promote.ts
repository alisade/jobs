// Promote an exported dev flow set to another environment.
//
// The release engineer who wrote this first cut handled the common case: queue ARNs that are the
// whole value of a QueueId parameter. Everything else (see README "Requirements") is TODO.
import { Artifact, DevExport, Inventory, Problem, PromotionResult, Replacement } from "./types";

export function promote(exp: DevExport, target: Inventory): PromotionResult {
  const replacements: Replacement[] = [];
  const problems: Problem[] = [];
  const artifacts: Artifact[] = [];

  const targetByName = new Map(target.resources.map((r) => [`${r.kind}:${r.name}`, r]));

  for (const f of exp.flows) {
    const flow = JSON.parse(f.ContactFlow.Content);
    for (const [i, action] of (flow.Actions || []).entries()) {
      const q = action.Parameters && action.Parameters.QueueId;
      if (typeof q !== "string") continue;
      const dev = exp.inventory.resources.find((r) => r.kind === "queue" && r.arn === q);
      if (!dev) continue;
      const tgt = targetByName.get(`queue:${dev.name}`);
      if (!tgt) continue; // TODO: report it
      action.Parameters.QueueId = tgt.arn;
      replacements.push({ artifact: f.ContactFlow.Name, path: `$.Actions[${i}].Parameters.QueueId`, from: q, to: tgt.arn, resource: `queue:${dev.name}` });
    }
    // TODO: every other reference kind, anywhere in the document (Metadata too), embedded in strings,
    //       bare resource ids, Lambda qualifiers, Lex aliases, modules, flows, the instance itself.
    // TODO: unknown references, references missing from the target, anything still pointing at dev.
    // TODO: modules (deploy before flows), target ids/ARNs, fail closed on problems.
    const tgtFlow = targetByName.get(`flow:${f.ContactFlow.Name}`);
    artifacts.push({
      kind: "flow",
      name: f.ContactFlow.Name,
      type: f.ContactFlow.Type,
      targetId: tgtFlow ? tgtFlow.id || null : null,
      targetArn: tgtFlow ? tgtFlow.arn : null,
      content: JSON.stringify(flow),
    });
  }

  return { ok: problems.length === 0, artifacts, replacements, problems };
}
