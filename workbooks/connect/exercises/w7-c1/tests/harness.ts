// Test harness for w7-c1: a fake ServiceNow (connect-kit), a mocked Customer Profiles client and
// a virtual clock so Retry-After waits do not slow the suite down.
import * as fs from "fs";
import * as path from "path";
import { mockClient } from "aws-sdk-client-mock";
import { CustomerProfilesClient, SearchProfilesCommand } from "@aws-sdk/client-customer-profiles";
import { startFakeServiceNow, FakeServiceNow, DEFAULT_CLIENT } from "connect-kit";

const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
// eslint-disable-next-line @typescript-eslint/no-var-requires
export const mod = require(path.join(root, "src/handler")) as typeof import("../src/handler");
// eslint-disable-next-line @typescript-eslint/no-var-requires
export const snmod = require(path.join(root, "src/servicenow")) as typeof import("../src/servicenow");

export const baseEvent = () => JSON.parse(fs.readFileSync(path.join(root, "events/connect-invoke.json"), "utf8"));
export const CONTACT_ID = "6a1f0c2e-8d4b-4f7e-b3a9-0c5d2e7f9a11";

export function virtualClock() {
  let offset = 0;
  const waits: number[] = [];
  return {
    waits,
    now: () => Date.now() + offset,
    sleep: async (ms: number) => {
      waits.push(ms);
      offset += ms;
    },
  };
}

export const seedUsers = [
  { sys_id: "a1b2c3d4e5f60718293a4b5c6d7e8f90", user_name: "priya.raman", employee_number: "E10442", vip: "false", active: "true" },
  { sys_id: "b1b2c3d4e5f60718293a4b5c6d7e8f91", user_name: "dana.okafor", employee_number: "E20001", vip: "true", active: "true" },
  { sys_id: "c1b2c3d4e5f60718293a4b5c6d7e8f92", user_name: "old.account", employee_number: "E10442", vip: "false", active: "false" },
];

export function incidentsFor(caller: string, n: number, extra: Record<string, string>[] = []) {
  const rows = [];
  for (let i = 0; i < n; i++) {
    rows.push({ number: `INC00${2000 + i}`, caller_id: caller, active: "true", state: "2", short_description: `Open issue ${i}`, correlation_id: "", sys_created_on: `2026-10-0${1 + (i % 8)} 10:${String(10 + i).padStart(2, "0")}:00` });
  }
  return rows.concat(extra as any);
}

export type Env = {
  sn: FakeServiceNow;
  profiles: ReturnType<typeof mockClient>;
  clock: ReturnType<typeof virtualClock>;
  handler: (e: any) => Promise<Record<string, any>>;
  client: InstanceType<typeof snmod.ServiceNowClient>;
};

export async function setup(opts: { incidents?: Record<string, string>[]; faults?: any; pageSize?: number; profileItems?: any[]; budgetMs?: number } = {}): Promise<Env> {
  const sn = await startFakeServiceNow({
    seed: { sys_user: seedUsers, incident: opts.incidents ?? incidentsFor(seedUsers[0].sys_id, 3, [{ number: "INC0001900", caller_id: seedUsers[0].sys_id, active: "false", state: "7", short_description: "closed", correlation_id: "", sys_created_on: "2026-09-01 09:00:00" }]) },
    faults: opts.faults,
  });
  const profiles = mockClient(CustomerProfilesClient);
  profiles.on(SearchProfilesCommand).resolves({ Items: (opts.profileItems ?? [{ ProfileId: "p-01", AccountNumber: "E10442", FirstName: "Priya", LastName: "Raman", PhoneNumber: "+12125550187" }]) as any });
  const clock = virtualClock();
  const client = new snmod.ServiceNowClient({ baseUrl: sn.url, clientId: DEFAULT_CLIENT.clientId, clientSecret: DEFAULT_CLIENT.clientSecret, pageSize: opts.pageSize, clock });
  const handler = mod.makeHandler({ profiles: new CustomerProfilesClient({ region: "us-east-1" }), domainName: "lfg-employees", sn: client, clock, budgetMs: opts.budgetMs });
  return { sn, profiles, clock, handler, client };
}

export async function teardown(env: Env) {
  env.profiles.restore();
  await env.sn.stop();
}

/** The fake stores what you POST; real ServiceNow also defaults active=true and state=1 on a new incident. */
export function applyServiceNowDefaults(env: Env) {
  for (const r of env.sn.db.incident || []) {
    if (r.active === undefined) r.active = "true";
    if (r.state === undefined) r.state = "1";
  }
}
