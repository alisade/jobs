// Release pipeline step "promote": rewrite environment-specific references in a dev export for a
// target environment. Written for release 2026.08 by the platform team (REL-388).
import { Inventory, Resource } from "./types";

// ARN tokens we rewrite: ANY service. Release 2026.10.06 was the first to reference a Lex V2 bot
// alias (arn:aws:lex:...), which the old (connect|lambda) allow-list silently passed through.
// Whether a token is rewritten is decided by the inventory, not by a list of services.
const ARN_RE = /arn:aws[a-z-]*:[a-z0-9-]+:[a-z0-9-]*:\d{12}:[A-Za-z0-9_\-./:+=@]+/g;
const UUID_RE = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g;

export interface RewriteResult {
  content: string;
  replaced: number;
}

function index(dev: Inventory, target: Inventory) {
  const tgt = new Map(target.resources.map((r) => [`${r.kind}:${r.name}`, r]));
  const byArn = new Map<string, string>();
  const lambdaBase = new Map<string, string>();
  const byId = new Map<string, string>();
  byArn.set(dev.instanceArn, target.instanceArn);
  byId.set(dev.instanceId, target.instanceId);
  for (const r of dev.resources) {
    const t: Resource | undefined = tgt.get(`${r.kind}:${r.name}`);
    if (!t) continue;
    if (r.kind === "lambda") lambdaBase.set(r.arn, t.arn);
    else byArn.set(r.arn, t.arn);
    if (r.id && t.id) byId.set(r.id, t.id);
  }
  return { byArn, lambdaBase, byId };
}

export function rewriteArtifact(content: string, dev: Inventory, target: Inventory): RewriteResult {
  const { byArn, lambdaBase, byId } = index(dev, target);
  let replaced = 0;
  const rewriteString = (s: string): string => {
    let out = s.replace(ARN_RE, (tok) => {
      if (byArn.has(tok)) {
        replaced++;
        return byArn.get(tok)!;
      }
      const m = /^(arn:aws[a-z-]*:lambda:[a-z0-9-]+:\d{12}:function:[A-Za-z0-9_-]+)(:[A-Za-z0-9_$-]+)?$/.exec(tok);
      if (m && lambdaBase.has(m[1])) {
        replaced++;
        return lambdaBase.get(m[1])! + (m[2] || "");
      }
      return tok;
    });
    out = out.replace(UUID_RE, (tok, offset: number, whole: string) => {
      if (!byId.has(tok)) return tok;
      const before = whole.slice(Math.max(0, whole.lastIndexOf("arn:", offset)), offset);
      if (before.startsWith("arn:") && !/[\s,"]/.test(before)) return tok;
      replaced++;
      return byId.get(tok)!;
    });
    return out;
  };
  const walk = (n: unknown): unknown => {
    if (typeof n === "string") return rewriteString(n);
    if (Array.isArray(n)) return n.map(walk);
    if (n && typeof n === "object") return Object.fromEntries(Object.entries(n as object).map(([k, v]) => [k, walk(v)]));
    return n;
  };
  return { content: JSON.stringify(walk(JSON.parse(content))), replaced };
}
