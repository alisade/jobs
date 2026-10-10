// Hidden tests for connect/w4-c1: full path matrix over the shipped scripts plus three unseen ones.
import * as path from "path";
import { translateAvaya } from "../../src/translate/avaya";
import { translateCisco } from "../../src/translate/cisco";
import { translateFive9 } from "../../src/translate/five9";
import { parseVector, runVector } from "../../src/legacy/avaya";
import { parseIcm, runIcm } from "../../src/legacy/cisco";
import { parseFive9, runFive9 } from "../../src/legacy/five9";
import { lintErrors } from "../../src/harness";
import { mapping, read, mismatches } from "../matrix";

const fx = (f: string) => read(path.join(__dirname, "fixtures", f));

type Case = { name: string; src: string; tr: (s: string, m: any) => any; legacy: (src: string) => (c: any) => any; digits: (string | null)[][] };
const cases: Case[] = [
  {
    name: "Avaya vector 14 (shipped)", src: read("legacy/avaya/vector-14-hd-main.txt"), tr: translateAvaya,
    legacy: (s) => { const v = parseVector(s); return (c) => runVector(v, c, mapping); },
    digits: [["1"], ["2"], ["3"], [null], ["9"]],
  },
  {
    name: "Avaya vector 21 (unseen)", src: fx("vector-21-vip.txt"), tr: translateAvaya,
    legacy: (s) => { const v = parseVector(s); return (c) => runVector(v, c, mapping); },
    digits: [["1"], ["2"], [null], ["5"]],
  },
  {
    name: "Cisco LFG_HD_Main (shipped)", src: read("legacy/cisco/LFG_HD_Main.icm.xml"), tr: translateCisco,
    legacy: (s) => { const v = parseIcm(s); return (c) => runIcm(v, c, mapping); },
    digits: [["1"], ["2"], ["3"], [null], ["8"]],
  },
  {
    name: "Cisco LFG_HD_Exec (unseen)", src: fx("LFG_HD_Exec.icm.xml"), tr: translateCisco,
    legacy: (s) => { const v = parseIcm(s); return (c) => runIcm(v, c, mapping); },
    digits: [["123456"], [null], ["3"], ["1"], ["2"]],
  },
  {
    name: "Five9 LFG HD Inbound (shipped)", src: read("legacy/five9/LFG_HD_Inbound.five9.xml"), tr: translateFive9,
    legacy: (s) => { const v = parseFive9(s); return (c) => runFive9(v, c, mapping); },
    digits: [["1"], ["2"], [null, null, null], ["4", "4", "1"], ["4", null, "2"]],
  },
  {
    name: "Five9 LFG HD Outage (unseen)", src: fx("LFG_HD_Outage.five9.xml"), tr: translateFive9,
    legacy: (s) => { const v = parseFive9(s); return (c) => runFive9(v, c, mapping); },
    digits: [["4242", "1"], ["4242", "9"], [null], ["4242", "3", "3"], ["4242", null, "1"]],
  },
];

for (const c of cases) {
  describe(c.name, () => {
    let flow: any;
    let err: unknown = null;
    try { flow = c.tr(c.src, mapping); } catch (e) { err = e; }
    test("translates and is lint clean", () => {
      expect(err).toBeNull();
      expect(lintErrors(flow)).toEqual([]);
    });
    test("starts with flow logging enabled", () => {
      expect(err).toBeNull();
      const start = flow.Actions.find((a: any) => a.Identifier === flow.StartAction);
      expect(start.Type).toBe("UpdateFlowLoggingBehavior");
    });
    for (const d of c.digits) {
      test(`path matrix digits=${JSON.stringify(d)} matches the legacy script`, () => {
        expect(err).toBeNull();
        expect(mismatches(c.legacy(c.src), flow, d).slice(0, 5)).toEqual([]);
      });
    }
  });
}

test("an unsupported construct fails loudly instead of being dropped (agent threshold > 0 cannot map)", () => {
  const bad = "01 goto step 3 if available-agents in skill 210 > 2\n02 queue-to skill 210 pri m\n03 disconnect after announcement none\n";
  expect(() => translateAvaya(bad, mapping)).toThrow();
});
