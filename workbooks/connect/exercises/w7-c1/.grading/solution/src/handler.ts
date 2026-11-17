// lfg-servicenow-incident: invoked from the help desk inbound flow (Invoke AWS Lambda function,
// synchronous, STRING_MAP response). Identifies the caller via Customer Profiles, finds the
// employee in ServiceNow, counts their open incidents and (for action=lookupOrCreate) opens an
// incident for this contact exactly once.
import type { ConnectContactFlowEvent } from "aws-lambda";
import { CustomerProfilesClient, SearchProfilesCommand } from "@aws-sdk/client-customer-profiles";
import { BudgetExceeded, Clock, ServiceNowClient, q, realClock } from "./servicenow";

export type Deps = {
  profiles: CustomerProfilesClient;
  domainName: string;
  sn: ServiceNowClient;
  clock?: Clock;
  budgetMs?: number;
};

type SysUser = { sys_id: string; user_name: string; employee_number: string; vip: string };
type Incident = { sys_id: string; number: string; short_description: string; correlation_id: string; state: string };

export type FlowResponse = Record<string, string>;

const flat = (o: Record<string, string | number | boolean>): FlowResponse =>
  Object.fromEntries(Object.entries(o).map(([k, v]) => [k, String(v)]));

export function makeHandler(deps: Deps) {
  const clock = deps.clock ?? realClock;
  const budgetMs = deps.budgetMs ?? 6500;
  return async (event: ConnectContactFlowEvent): Promise<FlowResponse> => {
    const started = clock.now();
    const deadline = started + budgetMs;
    const contact = event?.Details?.ContactData;
    const params = (event?.Details?.Parameters || {}) as Record<string, string>;
    const phone = contact?.CustomerEndpoint?.Address;
    const contactId = contact?.ContactId;
    if (!contactId || !phone || !/^\+[1-9]\d{6,14}$/.test(phone)) return flat({ status: "BAD_REQUEST", employeeFound: "false" });
    const action = params.action === "lookupOrCreate" ? "lookupOrCreate" : "lookup";

    let employeeNumber: string;
    try {
      const found = await deps.profiles.send(new SearchProfilesCommand({ DomainName: deps.domainName, KeyName: "_phone", Values: [phone] }));
      const items = found.Items || [];
      if (items.length === 0) return flat({ status: "NOT_FOUND", employeeFound: "false" });
      if (items.length > 1) return flat({ status: "AMBIGUOUS", employeeFound: "false", profileCount: items.length });
      employeeNumber = items[0].AccountNumber || "";
      if (!employeeNumber) return flat({ status: "NOT_FOUND", employeeFound: "false" });
    } catch {
      return flat({ status: "DEGRADED", employeeFound: "false", reason: "profiles" });
    }

    try {
      const users = await deps.sn.listAll<SysUser>("sys_user", `employee_number=${q(employeeNumber)}^active=true`, ["sys_id", "user_name", "employee_number", "vip"], deadline);
      if (users.length !== 1) return flat({ status: "NOT_FOUND", employeeFound: "false", employeeId: employeeNumber });
      const user = users[0];
      const open = await deps.sn.listAll<Incident>(
        "incident",
        `caller_id=${q(user.sys_id)}^active=true^ORDERBYDESCsys_created_on`,
        ["sys_id", "number", "short_description", "correlation_id", "state"],
        deadline,
      );
      const mine = open.find((i) => i.correlation_id === contactId);
      const base = {
        status: "OK",
        employeeFound: "true",
        employeeId: employeeNumber,
        vip: user.vip === "true" ? "true" : "false",
        openIncidentCount: open.length,
        latestOpenIncident: open[0]?.number || "",
      };
      if (action === "lookup") return flat({ ...base, incidentCreated: "false" });
      if (mine) return flat({ ...base, incidentCreated: "false", incidentNumber: mine.number, incidentSysId: mine.sys_id });
      const created = await deps.sn.create<Incident>(
        "incident",
        {
          caller_id: user.sys_id,
          short_description: (params.shortDescription || "Help desk call").slice(0, 160),
          category: params.category || "inquiry",
          contact_type: "phone",
          correlation_id: contactId,
          correlation_display: "AmazonConnect",
        },
        deadline,
      );
      return flat({ ...base, openIncidentCount: open.length + 1, incidentCreated: "true", incidentNumber: created.number, incidentSysId: created.sys_id });
    } catch (err) {
      const reason = err instanceof BudgetExceeded ? "budget" : "servicenow";
      return flat({ status: "DEGRADED", employeeFound: "false", employeeId: employeeNumber, reason });
    }
  };
}

// Production wiring (module scope: the token cache survives warm invocations).
let cached: ((e: ConnectContactFlowEvent) => Promise<FlowResponse>) | null = null;
export const handler = async (event: ConnectContactFlowEvent): Promise<FlowResponse> => {
  if (!cached) {
    cached = makeHandler({
      profiles: new CustomerProfilesClient({ maxAttempts: 2 }),
      domainName: process.env.PROFILES_DOMAIN || "lfg-employees",
      sn: new ServiceNowClient({
        baseUrl: process.env.SN_BASE_URL || "https://larkspur.service-now.com",
        clientId: process.env.SN_CLIENT_ID || "",
        clientSecret: process.env.SN_CLIENT_SECRET || "",
      }),
    });
  }
  return cached(event);
};
