// Visible tests for connect/w4-c1. The grader runs a much larger path matrix and unseen scripts.
import { translateAvaya } from "../src/translate/avaya";
import { translateCisco } from "../src/translate/cisco";
import { translateFive9 } from "../src/translate/five9";
import { parseVector, runVector } from "../src/legacy/avaya";
import { parseIcm, runIcm } from "../src/legacy/cisco";
import { parseFive9, runFive9 } from "../src/legacy/five9";
import { lintErrors, runConnect, call } from "../src/harness";
import { mapping, read, mismatches } from "./matrix";

const vec = read("legacy/avaya/vector-14-hd-main.txt");
const icm = read("legacy/cisco/LFG_HD_Main.icm.xml");
const f9 = read("legacy/five9/LFG_HD_Inbound.five9.xml");

describe("Avaya vector 14", () => {
  test("translated flow is lint clean", () => {
    expect(lintErrors(translateAvaya(vec, mapping))).toEqual([]);
  });
  test("open hours, option 1 with a password-reset agent available: same outcome", () => {
    const c = call({ digits: ["1"] }, mapping);
    expect(runConnect(translateAvaya(vec, mapping), c, mapping)).toEqual(runVector(parseVector(vec), c, mapping));
  });
  test("after hours and holiday paths match the vector", () => {
    expect(mismatches((c) => runVector(parseVector(vec), c, mapping), translateAvaya(vec, mapping), [null], { times: ["21:30"], holidays: [false, true] })).toEqual([]);
  });
});

describe("Cisco ICM LFG_HD_Main", () => {
  test("translated flow is lint clean", () => {
    expect(lintErrors(translateCisco(icm, mapping))).toEqual([]);
  });
  test("option 3 goes to the MajorIncident precision queue at priority 1", () => {
    const c = call({ digits: ["3"] }, mapping);
    expect(runConnect(translateCisco(icm, mapping), c, mapping)).toEqual(runIcm(parseIcm(icm), c, mapping));
  });
});

describe("Five9 LFG HD Inbound", () => {
  test("translated flow is lint clean", () => {
    expect(lintErrors(translateFive9(f9, mapping))).toEqual([]);
  });
  test("menu retries (two bad keys, then 1) match the legacy script", () => {
    const c = call({ digits: ["7", null, "1"] }, mapping);
    expect(runConnect(translateFive9(f9, mapping), c, mapping)).toEqual(runFive9(parseFive9(f9), c, mapping));
  });
});
