// POST /v1/opportunities/:id/transitions  (pipeline-svc)
// One transaction: tenant + role set locally, row locked, rules checked, opportunity updated,
// stage_history and outbox rows written. Either all of it commits or none of it does.
import { randomUUID } from "crypto";
import { sql } from "kysely";
import { z } from "zod";
import type { FastifyInstance } from "fastify";
import type { AppOptions } from "./app";
import { withTenant } from "./db";
import { ProblemError } from "./problems";
import { STAGES, Stage } from "./types";

export const ALLOWED: Record<Stage, Stage[]> = {
  prospecting: ["qualification", "closed_lost"],
  qualification: ["proposal", "closed_lost"],
  proposal: ["negotiation", "qualification", "closed_lost"],
  negotiation: ["closed_won", "closed_lost", "proposal"],
  closed_won: [],
  closed_lost: [],
};

const Body = z.object({
  to_stage: z.enum(STAGES),
  expected_version: z.number().int().positive(),
  close_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "expected YYYY-MM-DD").optional(),
}).strict();

const isoDate = (d: Date | string | null): string | null =>
  d === null ? null : (d instanceof Date ? d.toISOString().slice(0, 10) : String(d).slice(0, 10));

export function registerTransitions(app: FastifyInstance, opts: AppOptions): void {
  const { db } = opts.db;
  const hooks = opts.hooks || {};

  app.post<{ Params: { id: string } }>("/v1/opportunities/:id/transitions", async (req) => {
    const tenant = req.headers["x-tenant-id"];
    if (typeof tenant !== "string" || !tenant) throw new ProblemError(400, "missing-tenant", "X-Tenant-Id header is required");
    const actor = typeof req.headers["x-user-id"] === "string" ? (req.headers["x-user-id"] as string) : "system";
    const id = Number(req.params.id);
    if (!Number.isSafeInteger(id) || id <= 0) {
      throw new ProblemError(400, "validation-error", "Request is invalid", "id must be a positive integer",
        { errors: [{ path: "id", message: "must be a positive integer" }] });
    }
    const parsed = Body.safeParse(req.body);
    if (!parsed.success) {
      throw new ProblemError(400, "validation-error", "Request body is invalid", "See errors.",
        { errors: parsed.error.issues.map((i) => ({ path: i.path.join("."), message: i.message })) });
    }
    const body = parsed.data;

    return withTenant(db, tenant, async (trx) => {
      // RLS hides other tenants' rows, so "not yours" and "does not exist" are the same 404.
      const opp = await trx.selectFrom("opportunities").selectAll().where("id", "=", id).forUpdate().executeTakeFirst();
      if (!opp) throw new ProblemError(404, "not-found", "Opportunity not found");
      if (hooks.afterLock) await hooks.afterLock();

      if (opp.version !== body.expected_version) {
        throw new ProblemError(409, "version-conflict", "Opportunity was changed by someone else",
          `expected version ${body.expected_version}, current version ${opp.version}`, { current_version: opp.version });
      }
      const from = opp.stage as Stage;
      const to = body.to_stage;
      if (!ALLOWED[from].includes(to)) {
        throw new ProblemError(422, "illegal-transition", "Stage transition not allowed",
          `${from} -> ${to} is not allowed`, { from_stage: from, to_stage: to, allowed: ALLOWED[from] });
      }
      let closeDate = body.close_date ?? isoDate(opp.close_date);
      if (to === "closed_won") {
        const missing: string[] = [];
        if (!(Number(opp.amount) > 0)) missing.push("amount must be greater than 0");
        if (!closeDate) missing.push("close_date is required");
        if (missing.length) {
          throw new ProblemError(422, "closed-won-requirements", "Cannot close as won", missing.join("; "), { errors: missing });
        }
      }
      if (to === "closed_lost" && !closeDate) closeDate = new Date().toISOString().slice(0, 10);

      const version = opp.version + 1;
      await trx.updateTable("opportunities")
        .set({ stage: to, version, close_date: closeDate, updated_at: sql`now()` })
        .where("id", "=", id).where("version", "=", opp.version)
        .execute();
      await trx.insertInto("stage_history").values({
        tenant_id: tenant, opportunity_id: id, from_stage: from, to_stage: to, version, changed_by: actor,
      }).execute();
      const eventId = randomUUID();
      await trx.insertInto("outbox").values({
        event_id: eventId,
        tenant_id: tenant,
        aggregate_type: "opportunity",
        aggregate_id: String(id),
        type: "OpportunityStageChanged",
        payload: JSON.stringify({
          event_id: eventId, opportunity_id: id, account_id: Number(opp.account_id),
          from_stage: from, to_stage: to, version, changed_by: actor,
        }),
        published_at: null,
      }).execute();
      if (hooks.beforeCommit) await hooks.beforeCommit();
      return { id, stage: to, version, close_date: closeDate, event_id: eventId };
    });
  });
}
