// make eval: run the recorded eval set through src/triage.ts and print the gate result.
import * as path from "path";
import { replayClient, loadCases } from "../src/replay";
import { triage } from "../src/triage";
import { runEval, gate } from "../src/eval";

(async () => {
  const root = path.resolve(__dirname, "../..");
  const { client } = replayClient(root);
  const report = await runEval(loadCases(root), (t) => triage(t, client));
  console.log(JSON.stringify(report, null, 2));
  const g = gate(report);
  console.log(g.pass ? "GATE: PASS" : `GATE: FAIL - ${g.reasons.join("; ")}`);
})();
