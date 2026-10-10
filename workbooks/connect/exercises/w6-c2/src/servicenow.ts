// Provided: a small ServiceNow Table API client (OAuth client credentials) for work notes.
export interface SnConfig { baseUrl: string; clientId: string; clientSecret: string }

export class WorkNotesClient {
  private token: string | null = null;
  constructor(private cfg: SnConfig) {}

  private async auth(): Promise<string> {
    if (this.token) return this.token;
    const res = await fetch(`${this.cfg.baseUrl}/oauth_token.do`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ grant_type: "client_credentials", client_id: this.cfg.clientId, client_secret: this.cfg.clientSecret }),
    });
    if (!res.ok) throw new Error(`ServiceNow token: ${res.status}`);
    this.token = ((await res.json()) as { access_token: string }).access_token;
    return this.token;
  }

  /** Append a work note to an incident (PATCH work_notes). Throws on non-2xx. */
  async addWorkNote(incidentSysId: string, note: string): Promise<void> {
    const res = await fetch(`${this.cfg.baseUrl}/api/now/table/incident/${incidentSysId}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${await this.auth()}`, "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ work_notes: note }),
    });
    if (!res.ok) throw new Error(`ServiceNow work note on ${incidentSysId}: ${res.status}`);
  }
}
