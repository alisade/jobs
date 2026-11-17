// Backend for the workspace app: a small REST API (API Gateway + Lambda in production) that
// updates the ServiceNow incident on the agent's behalf. The app never talks to ServiceNow directly.

export type IncidentUpdate = { work_notes: string; state?: string; close_code?: string; close_notes?: string };

export interface IncidentApi {
  updateIncident(sysId: string, update: IncidentUpdate): Promise<{ number: string; state: string }>;
}

// TODO: auth header, sys_id validation, error handling (see README "Backend").
export function createIncidentApi(baseUrl: string, _getToken: () => Promise<string>, fetchImpl: typeof fetch = fetch): IncidentApi {
  return {
    async updateIncident(sysId, update) {
      const res = await fetchImpl(`${baseUrl}/incidents/${sysId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(update),
      });
      return (await res.json()) as { number: string; state: string };
    },
  };
}
