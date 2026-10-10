// Hidden tests for connect/x-3 (copied to tests/__hidden__ by the grader).
import * as path from "path";
import { recognize } from "../../tools/nlu";
import { bot, cases, evalCases, readJson } from "../harness";

const heldout = () => cases(path.join(__dirname, "fixtures", "heldout.csv"));
const failures = (rows: { utterance: string; intent: string; system: string }[]) => {
  const b = bot();
  return rows.filter((c) => {
    const r = recognize(b, c.utterance);
    const got = r.slots.System ? r.slots.System.interpretedValue : "";
    return r.intent !== c.intent || (c.system && got !== c.system);
  }).map((c) => c.utterance);
};

test("every utterance in the eval set gets the right intent and the CMDB code for the system", () => {
  expect(failures(evalCases())).toEqual([]);
});
test("held-out utterances (not in evals/) also work", () => {
  expect(failures(heldout())).toEqual([]);
});
test("outage statements no longer fall to FallbackIntent and score well above the threshold", () => {
  const b = bot();
  for (const u of ["vpn is down", "is outlook down", "sap is down"]) {
    const r = recognize(b, u);
    expect(r.intent).toBe("ReportOutage");
    expect(r.confidence!).toBeGreaterThanOrEqual(0.8);
  }
});
test("the confidence threshold was not lowered to hide the problem", () => {
  expect(readJson("BotLocales/en_US/BotLocale.json").nluConfidenceThreshold).toBeCloseTo(0.4, 5);
});
test("slot type values stay the CMDB codes the ServiceNow integration needs", () => {
  const st = readJson("BotLocales/en_US/SlotTypes/SystemName/SlotType.json");
  const values = st.slotTypeValues.map((v: any) => v.sampleValue.value).sort();
  expect(values).toEqual(["CI-EXCHANGE-ONLINE", "CI-GLOBALPROTECT", "CI-OKTA-PROD", "CI-SAP-ECC", "CI-WORKDAY"]);
});
test("every CMDB code has spoken synonyms and resolves to the code (top resolution)", () => {
  const st = readJson("BotLocales/en_US/SlotTypes/SystemName/SlotType.json");
  for (const v of st.slotTypeValues) expect((v.synonyms || []).length).toBeGreaterThan(0);
  expect(String(st.valueSelectionSetting.resolutionStrategy).replace(/_/g, "").toLowerCase()).toBe("topresolution");
});
test("guard: generic intents still work", () => {
  const b = bot();
  expect(recognize(b, "what is the status of my ticket").intent).toBe("CheckTicketStatus");
  expect(recognize(b, "locked out").intent).toBe("UnlockAccount");
});
