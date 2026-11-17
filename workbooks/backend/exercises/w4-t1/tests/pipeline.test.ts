// Visible tests for backend/w4-t1: the pipeline view works and is batched.
import { seedStore } from "../src/store";
import { pipeline, accountNames } from "./helpers";

test("the pipeline view resolves each opportunity's account", async () => {
  const store = seedStore();
  const rows = await pipeline(store, "bu-emea", "u-ines", "u-ines");
  expect(accountNames(rows)).toEqual(["Fjordline AS", "Orbital Freight"]);
});

test("accounts are batched: one accounts-svc call for 20 opportunities", async () => {
  const store = seedStore();
  const rows = await pipeline(store, "bu-amer", "u-mark", "u-mark");
  expect(rows).toHaveLength(20);
  expect(store.queryLog.filter((q) => q.service === "accounts-svc")).toHaveLength(1);
});
