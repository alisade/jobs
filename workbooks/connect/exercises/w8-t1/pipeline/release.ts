// make release: dev export -> release/prod/*.json via rewrite.ts, then the check-refs gate.
// Exit 1 when the gate finds problems (artifacts are still written so you can inspect them).
import * as fs from "fs";
import * as path from "path";
import { rewriteArtifact } from "./rewrite";
import { checkRefs } from "./check-refs";
import { Inventory } from "./types";

const root = path.resolve(__dirname, "..");
const read = (p: string) => JSON.parse(fs.readFileSync(p, "utf8"));
const dev: Inventory = read(path.join(root, "export/dev/inventory.json"));
const target: Inventory = read(path.join(root, "inventory/prod.json"));
const out = path.join(root, "release/prod");
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });

type Item = { kind: "module" | "flow"; name: string; type?: string; content: string };
const items: Item[] = [];
for (const f of fs.readdirSync(path.join(root, "export/dev/modules")).sort()) {
  const m = read(path.join(root, "export/dev/modules", f)).ContactFlowModule;
  items.push({ kind: "module", name: m.Name, content: m.Content });
}
for (const f of fs.readdirSync(path.join(root, "export/dev/flows")).sort()) {
  const c = read(path.join(root, "export/dev/flows", f)).ContactFlow;
  items.push({ kind: "flow", name: c.Name, type: c.Type, content: c.Content });
}
let total = 0;
let problems = 0;
items.forEach((it, i) => {
  const r = rewriteArtifact(it.content, dev, target);
  total += r.replaced;
  const t = target.resources.find((x) => x.kind === it.kind && x.name === it.name);
  const artifact = { kind: it.kind, name: it.name, type: it.type, targetId: t ? t.id : null, content: r.content };
  const file = `${String(i + 1).padStart(2, "0")}-${it.kind}-${it.name.replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()}.json`;
  fs.writeFileSync(path.join(out, file), JSON.stringify(artifact, null, 2) + "\n");
  for (const p of checkRefs(it.name, r.content, target)) {
    problems++;
    console.log(`check-refs: ${p.reason} ${p.artifact} ${p.path} ${p.arn}`);
  }
});
console.log(`promote: ${items.length} artifacts, ${total} references rewritten; check-refs: ${problems} problem(s)`);
process.exit(problems ? 1 : 0);
