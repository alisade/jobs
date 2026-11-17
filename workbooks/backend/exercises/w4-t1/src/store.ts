// Stand-ins for the two services the pipeline read layer calls. In production these are HTTP calls to
// accounts-svc and pipeline-svc; here they are in memory with a small latency, and every call is
// recorded in queryLog so you can see what ran, for whom, with which ids.
// Account ids are unique per tenant only (composite (tenant_id, id) keys, migrated from the CRM), so
// the same id can exist in two tenants.

export interface Auth { tenantId: string; userId: string }
export interface Account { id: string; tenantId: string; name: string; ownerId: string }
export interface Opportunity { id: string; tenantId: string; accountId: string; ownerId: string; name: string; stage: string; amount: number }
export interface QueryLogEntry { service: string; op: string; tenant: string; ids?: string[]; at: number }

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export class Store {
  accounts: Account[] = [];
  opportunities: Opportunity[] = [];
  queryLog: QueryLogEntry[] = [];
  private seq = 0;

  // accounts-svc: GET /v1/accounts:batchGet?ids=... (tenant from the caller's token; others are not found)
  async batchGetAccounts(auth: Auth, ids: readonly string[]): Promise<(Account | null)[]> {
    this.queryLog.push({ service: "accounts-svc", op: "batchGet", tenant: auth.tenantId, ids: [...ids], at: this.seq++ });
    await sleep(5);
    return ids.map((id) => { const a = this.accounts.find((x) => x.tenantId === auth.tenantId && x.id === id); return a ? { ...a } : null; });
  }

  // pipeline-svc: GET /v1/opportunities?owner=...
  async listOpportunities(auth: Auth, ownerId?: string): Promise<Opportunity[]> {
    this.queryLog.push({ service: "pipeline-svc", op: "list", tenant: auth.tenantId, at: this.seq++ });
    await sleep(5);
    return this.opportunities.filter((o) => o.tenantId === auth.tenantId && (!ownerId || o.ownerId === ownerId));
  }

  renameAccount(tenantId: string, id: string, name: string): void {
    const a = this.accounts.find((x) => x.tenantId === tenantId && x.id === id);
    if (!a) throw new Error(`no account ${tenantId}/${id}`);
    a.name = name;
  }
}

// Synthetic data: account 1042 exists in bu-emea (Fjordline AS) and in bu-amer (Cedar Grid Inc).
export function seedStore(): Store {
  const s = new Store();
  const acct = (tenantId: string, id: string, name: string, ownerId: string) => s.accounts.push({ id, tenantId, name, ownerId });
  acct("bu-emea", "1042", "Fjordline AS", "u-ines");
  acct("bu-emea", "1043", "Orbital Freight", "u-ines");
  acct("bu-amer", "1042", "Cedar Grid Inc", "u-dana");
  acct("bu-amer", "1044", "Harbor Labs", "u-dana");
  for (let i = 1; i <= 20; i++) acct("bu-amer", String(2000 + i), `Amer Account ${i}`, "u-dana");
  let n = 1;
  const opp = (tenantId: string, accountId: string, ownerId: string, name: string, stage: string, amount: number) =>
    s.opportunities.push({ id: String(n++), tenantId, accountId, ownerId, name, stage, amount });
  opp("bu-emea", "1042", "u-ines", "Fjordline fleet analytics", "proposal", 120000);
  opp("bu-emea", "1043", "u-ines", "Orbital Freight renewal", "negotiation", 480000);
  opp("bu-amer", "1042", "u-dana", "Cedar Grid platform", "qualification", 90000);
  opp("bu-amer", "1044", "u-dana", "Harbor Labs pilot", "prospecting", 15000);
  for (let i = 1; i <= 20; i++) opp("bu-amer", String(2000 + i), "u-mark", `Amer deal ${i}`, "proposal", 1000 * i);
  return s;
}
