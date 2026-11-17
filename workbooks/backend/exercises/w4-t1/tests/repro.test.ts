// make repro: replay the ticket. Prints what each request saw; always passes (it is a tool, not a check).
import { seedStore } from "../src/store";
import { pipeline, accountNames } from "./helpers";

test("repro: EMEA then AMER pipeline", async () => {
  const store = seedStore();
  const emea = await pipeline(store, "bu-emea", "u-ines", "u-ines");
  const amer = await pipeline(store, "bu-amer", "u-dana", "u-dana");
  console.log("REPRO bu-emea u-ines sees: " + JSON.stringify(accountNames(emea)));
  console.log("REPRO bu-amer u-dana sees: " + JSON.stringify(accountNames(amer)) + "  (expected [\"Cedar Grid Inc\",\"Harbor Labs\"])");
  console.log("REPRO accounts-svc calls: " + JSON.stringify(store.queryLog.filter((q) => q.service === "accounts-svc").map((q) => ({ tenant: q.tenant, ids: q.ids }))));
  expect(true).toBe(true);
});
