// Promote an exported dev flow set to another environment (reference solution).
//
// Join key: "<kind>:<logical name>" is the same in every environment, so a dev reference is
// resolved to a dev resource, then to the same-named resource in the target manifest.
import { Artifact, DevExport, Inventory, Problem, PromotionResult, Replacement, Resource } from "./types";

// An ARN token inside any string. Stops at characters that cannot be part of an ARN in a flow.
const ARN_RE = /arn:aws[a-z-]*:[a-z0-9-]+:[a-z0-9-]*:\d{12}:[A-Za-z0-9_\-./:+=@]+/g;
const UUID_RE = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g;
const ID_KEY = /^[A-Za-z_][A-Za-z0-9_]*$/;

type Mapping = { resource: string; to: string | null };

function childPath(path: string, key: string | number): string {
  if (typeof key === "number") return `${path}[${key}]`;
  return ID_KEY.test(key) ? `${path}.${key}` : `${path}[${JSON.stringify(key)}]`;
}

export function promote(exp: DevExport, target: Inventory): PromotionResult {
  const dev = exp.inventory;
  const replacements: Replacement[] = [];
  const problems: Problem[] = [];
  const targetByKey = new Map(target.resources.map((r) => [`${r.kind}:${r.name}`, r]));

  const mapRes = (r: Resource, field: "arn" | "id"): Mapping => {
    const key = `${r.kind}:${r.name}`;
    const t = targetByKey.get(key);
    return { resource: key, to: t ? (field === "id" ? t.id || null : t.arn) : null };
  };
  // ARN -> mapping (exact), Lambda base ARN -> mapping (qualifier preserved), bare id -> mapping.
  const byArn = new Map<string, Mapping>();
  const lambdaBase = new Map<string, Mapping>();
  const byId = new Map<string, Mapping>();
  byArn.set(dev.instanceArn, { resource: "instance", to: target.instanceArn });
  byId.set(dev.instanceId, { resource: "instance", to: target.instanceId });
  for (const r of dev.resources) {
    if (r.kind === "lambda") lambdaBase.set(r.arn, mapRes(r, "arn"));
    else byArn.set(r.arn, mapRes(r, "arn"));
    if (r.id) byId.set(r.id, mapRes(r, "id"));
  }

  function resolveArn(token: string): Mapping | "unknown" | "foreign" {
    const exact = byArn.get(token);
    if (exact) return exact;
    const m = /^(arn:aws[a-z-]*:lambda:[a-z0-9-]+:\d{12}:function:[A-Za-z0-9_-]+)(:[A-Za-z0-9_$-]+)?$/.exec(token);
    if (m && lambdaBase.has(m[1])) {
      const base = lambdaBase.get(m[1])!;
      return { resource: base.resource, to: base.to ? base.to + (m[2] || "") : null };
    }
    const devOwned = token.includes(`:${dev.accountId}:`) || token.includes(dev.instanceId);
    return devOwned ? "unknown" : "foreign";
  }

  function rewriteString(artifact: string, path: string, value: string): string {
    const reported = new Set<string>();
    const problem = (v: string, reason: Problem["reason"], detail: string) => {
      if (reported.has(v)) return;
      reported.add(v);
      problems.push({ artifact, path, value: v, reason, detail });
    };
    let out = value.replace(ARN_RE, (token) => {
      const r = resolveArn(token);
      if (r === "foreign") return token;
      if (r === "unknown") {
        problem(token, "unknown-reference", "dev ARN not in the dev inventory");
        return token;
      }
      if (!r.to) {
        problem(token, "unmapped-in-target", `${r.resource} does not exist in ${target.env}`);
        return token;
      }
      if (r.to !== token) replacements.push({ artifact, path, from: token, to: r.to, resource: r.resource });
      return r.to;
    });
    out = out.replace(UUID_RE, (token, offset: number, whole: string) => {
      const m = byId.get(token);
      if (!m) return token;
      // part of an ARN we left alone (unknown / unmapped): already reported
      const before = whole.slice(Math.max(0, whole.lastIndexOf("arn:", offset)), offset);
      if (before.startsWith("arn:") && !/[\s,"]/.test(before)) return token;
      if (!m.to) {
        problem(token, "unmapped-in-target", `${m.resource} does not exist in ${target.env}`);
        return token;
      }
      replacements.push({ artifact, path, from: token, to: m.to, resource: m.resource });
      return m.to;
    });
    // anything that still points at dev (account, instance, a dev resource id) is dangling
    if (!reported.size) {
      const devIds = [dev.instanceId, ...dev.resources.map((r) => r.id).filter(Boolean)] as string[];
      if (out.includes(`:${dev.accountId}:`) && dev.accountId !== target.accountId) problem(out, "dangling", `still references dev account ${dev.accountId}`);
      else if (devIds.some((id) => out.includes(id))) problem(out, "dangling", "still references a dev resource id");
    }
    return out;
  }

  function walk(artifact: string, node: unknown, path: string): unknown {
    if (typeof node === "string") return rewriteString(artifact, path, node);
    if (Array.isArray(node)) return node.map((v, i) => walk(artifact, v, childPath(path, i)));
    if (node && typeof node === "object") {
      const out: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(node as Record<string, unknown>)) out[k] = walk(artifact, v, childPath(path, k));
      return out;
    }
    return node;
  }

  const artifacts: Artifact[] = [];
  const build = (kind: "module" | "flow", name: string, content: string, type?: string) => {
    const rewritten = walk(name, JSON.parse(content), "$");
    const t = targetByKey.get(`${kind}:${name}`);
    artifacts.push({ kind, name, type, targetId: t ? t.id || null : null, targetArn: t ? t.arn : null, content: JSON.stringify(rewritten) });
  };
  const byName = <T>(get: (x: T) => string) => (a: T, b: T) => get(a).localeCompare(get(b));
  [...exp.modules].sort(byName((m) => m.ContactFlowModule.Name)).forEach((m) => build("module", m.ContactFlowModule.Name, m.ContactFlowModule.Content));
  [...exp.flows].sort(byName((f) => f.ContactFlow.Name)).forEach((f) => build("flow", f.ContactFlow.Name, f.ContactFlow.Content, f.ContactFlow.Type));

  const ok = problems.length === 0;
  return { ok, artifacts: ok ? artifacts : [], replacements, problems };
}
