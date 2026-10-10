// lfg-create-incident: invoked by the "LFG Help Desk Inbound" flow (InvokeLambdaFunction, time limit
// 8 s) after the bot has collected the issue, so the agent who answers already has a ticket number.
// Returns a flat string map (STRING_MAP): incidentNumber, incidentSysId, created, error.
import { ServiceNowClient } from "./servicenow";
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
  /** shared idempotency store (see idempotency.ts); unused by the 2026.08 release */
  store?: IdempotencyStore;
  sleep?: (ms: number) => Promise<void>;
}

export function createHandler(deps: Deps) {
  return async (event: ConnectEvent): Promise<Result> => {
    const c = event.Details.ContactData;
    const p = event.Details.Parameters;
    const body = {
      short_description: p.shortDescription || "Help desk call",
      description: p.description || "",
      caller_id: c.Attributes.employeeSysId || "",
      category: p.category || "inquiry",
      contact_type: c.Channel === "CHAT" ? "chat" : "phone",
      correlation_id: c.ContactId,
      correlation_display: "Amazon Connect",
    };
    try {
      const res = await deps.sn.request<{ result: { number: string; sys_id: string } }>(
        "POST", "/api/now/table/incident?sysparm_fields=number,sys_id", body);
      return { incidentNumber: res.result.number, incidentSysId: res.result.sys_id, created: "true", error: "" };
    } catch (err: any) {
      return { incidentNumber: "", incidentSysId: "", created: "false", error: String(err && err.message) };
    }
  };
}
