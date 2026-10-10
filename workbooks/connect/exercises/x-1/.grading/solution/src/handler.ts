// lfg-create-incident: invoked by the "LFG Help Desk Inbound" flow (InvokeLambdaFunction, time limit
// 8 s) after the bot has collected the issue, so the agent who answers already has a ticket number.
// Returns a flat string map (STRING_MAP): incidentNumber, incidentSysId, created, error.
//
// Idempotent per contact: the ContactId is the idempotency key (stored as the incident's
// correlation_id and as a claimed record in the idempotency table). A POST whose outcome is unknown
// (timeout, 502/503/504) is never blindly retried: we look for the incident first.
import { ServiceNowClient, ServiceNowError } from "./servicenow";
import { IdempotencyStore } from "./idempotency";

export interface ConnectEvent {
  Details: {
    ContactData: { ContactId: string; InitialContactId?: string; Attributes: Record<string, string>; Channel: string };
    Parameters: Record<string, string>;
  };
  Name: string;
}

export type Result = { incidentNumber: string; incidentSysId: string; created: "true" | "false"; error: string };

export interface Deps {
  sn: ServiceNowClient;
  store?: IdempotencyStore;
  sleep?: (ms: number) => Promise<void>;
}

type Inc = { number: string; sys_id: string };

export function createHandler(deps: Deps) {
  const sleep = deps.sleep ?? ((ms: number) => new Promise<void>((r) => setTimeout(r, ms)));

  const findByCorrelation = async (id: string): Promise<Inc | null> => {
    const q = encodeURIComponent(`correlation_id=${id}^ORDERBYsys_created_on`);
    const r = await deps.sn.request<{ result: Inc[] }>("GET", `/api/now/table/incident?sysparm_query=${q}&sysparm_fields=number,sys_id&sysparm_limit=1`);
    return r.result[0] || null;
  };

  return async (event: ConnectEvent): Promise<Result> => {
    const c = event.Details.ContactData;
    const p = event.Details.Parameters;
    const id = c.ContactId;
    const key = `create-incident#${id}`;
    const ok = async (inc: Inc, created: boolean): Promise<Result> => {
      const out: Result = { incidentNumber: inc.number, incidentSysId: inc.sys_id, created: created ? "true" : "false", error: "" };
      if (deps.store) await deps.store.complete(key, { incidentNumber: inc.number, incidentSysId: inc.sys_id });
      return out;
    };
    const body = {
      short_description: p.shortDescription || "Help desk call",
      description: p.description || "",
      caller_id: c.Attributes.employeeSysId || "",
      category: p.category || "inquiry",
      contact_type: c.Channel === "CHAT" ? "chat" : "phone",
      correlation_id: id,
      correlation_display: "Amazon Connect",
    };
    try {
      // 1. a previous invocation for this contact (Connect retry, flow loop) already finished
      if (deps.store) {
        const rec = await deps.store.get(key);
        if (rec && rec.status === "COMPLETED" && rec.result) {
          return { incidentNumber: rec.result.incidentNumber, incidentSysId: rec.result.incidentSysId, created: "false", error: "" };
        }
      }
      // 2. the incident exists already (record lost, or created by an earlier ambiguous attempt)
      const existing = await findByCorrelation(id);
      if (existing) return ok(existing, false);
      // 3. exactly one concurrent invocation may create; the others wait for its result
      if (deps.store && !(await deps.store.claim(key, 3600))) {
        for (let i = 0; i < 12; i++) {
          await sleep(250);
          const rec = await deps.store.get(key);
          if (rec && rec.status === "COMPLETED" && rec.result) {
            return { incidentNumber: rec.result.incidentNumber, incidentSysId: rec.result.incidentSysId, created: "false", error: "" };
          }
          const found = await findByCorrelation(id);
          if (found) return { incidentNumber: found.number, incidentSysId: found.sys_id, created: "false", error: "" };
        }
        return { incidentNumber: "", incidentSysId: "", created: "false", error: "create in progress by another invocation" };
      }
      // 4. create; on an ambiguous failure look before retrying
      let lastErr: unknown = null;
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const res = await deps.sn.request<{ result: Inc }>("POST", "/api/now/table/incident?sysparm_fields=number,sys_id", body, { retry: false });
          return ok(res.result, true);
        } catch (err) {
          lastErr = err;
          if (!(err instanceof ServiceNowError)) throw err;
          if (err.status === 429) {
            await sleep(500 * (attempt + 1));
            continue;
          }
          if (!err.ambiguous) throw err;
          const found = await findByCorrelation(id);
          if (found) return ok(found, true);
          await sleep(200 * (attempt + 1));
        }
      }
      throw lastErr;
    } catch (err: any) {
      return { incidentNumber: "", incidentSysId: "", created: "false", error: String(err && err.message) };
    }
  };
}
