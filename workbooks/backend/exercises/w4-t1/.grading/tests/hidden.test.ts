// Hidden tests for backend/w4-t1 (run from tests/__hidden__/).
import * as fs from "fs";
import * as path from "path";
import { seedStore } from "../../src/store";
import { createContext } from "../../src/context";
import { pipeline, accountNames } from "../helpers";

test("same account id in two tenants: the second tenant gets its own account, not the cached one", async () => {
  const store = seedStore();
  await pipeline(store, "bu-emea", "u-ines", "u-ines");
  const amer = await pipeline(store, "bu-amer", "u-dana", "u-dana");
  expect(accountNames(amer)).toEqual(["Cedar Grid Inc", "Harbor Labs"]);
});

test("interleaved requests from two tenants each see only their own accounts", async () => {
  const store = seedStore();
  const [emea, amer] = await Promise.all([
    pipeline(store, "bu-emea", "u-ines", "u-ines"),
    pipeline(store, "bu-amer", "u-dana", "u-dana"),
  ]);
  expect(accountNames(emea)).toEqual(["Fjordline AS", "Orbital Freight"]);
  expect(accountNames(amer)).toEqual(["Cedar Grid Inc", "Harbor Labs"]);
});

test("every accounts-svc batch runs with the auth of the request whose ids it carries", async () => {
  const store = seedStore();
  await Promise.all([
    pipeline(store, "bu-emea", "u-ines", "u-ines"),
    pipeline(store, "bu-amer", "u-dana", "u-dana"),
    pipeline(store, "bu-amer", "u-mark", "u-mark"),
  ]);
  const calls = store.queryLog.filter((q) => q.service === "accounts-svc");
  const emeaIds = calls.filter((c) => c.tenant === "bu-emea").flatMap((c) => c.ids || []).sort();
  const amerIds = calls.filter((c) => c.tenant === "bu-amer").flatMap((c) => c.ids || []);
  expect(emeaIds).toEqual(["1042", "1043"]);
  expect(amerIds).toEqual(expect.arrayContaining(["1042", "1044", "2001", "2020"]));
  expect(amerIds).not.toContain("1043");
});

test("a rename is visible on the next request (no cross-request cache)", async () => {
  const store = seedStore();
  await pipeline(store, "bu-emea", "u-ines", "u-ines");
  store.renameAccount("bu-emea", "1043", "Orbital Freight Group");
  const again = await pipeline(store, "bu-emea", "u-ines", "u-ines");
  expect(accountNames(again)).toEqual(["Fjordline AS", "Orbital Freight Group"]);
});

test("batching still works per request: one accounts-svc call per pipeline request", async () => {
  const store = seedStore();
  await pipeline(store, "bu-amer", "u-mark", "u-mark");
  await pipeline(store, "bu-amer", "u-mark", "u-mark");
  expect(store.queryLog.filter((q) => q.service === "accounts-svc")).toHaveLength(2);
});

test("each context gets its own loader instance", () => {
  const store = seedStore();
  const a = createContext({ tenantId: "bu-emea", userId: "u-ines" }, store);
  const b = createContext({ tenantId: "bu-amer", userId: "u-dana" }, store);
  expect(a.loaders.account).not.toBe(b.loaders.account);
});

test("ANSWER.md names the shared, process-wide loader as the root cause", () => {
  let d = __dirname;
  while (!d.endsWith("/tests")) d = path.dirname(d);
  const text = fs.readFileSync(path.join(path.dirname(d), "ANSWER.md"), "utf8").replace(/<!--[\s\S]*?-->/g, "");
  expect(text).toMatch(/per[- ]request/i);
  expect(text).toMatch(/module[- ]?(scope|level)|process[- ]wide|shared (data)?loader|singleton|global/i);
});
