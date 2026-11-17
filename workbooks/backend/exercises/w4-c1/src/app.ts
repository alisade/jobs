// pipeline-svc HTTP app (Fastify). buildApp() is used by the server and by the tests (fastify.inject).
import Fastify, { FastifyInstance } from "fastify";
import type { Db } from "./db";
import { withTenant } from "./db";
import { registerTransitions } from "./transitions";

export interface Hooks {
  // Test seams: called inside the transition transaction. Production passes nothing.
  afterLock?: () => Promise<void>;
  beforeCommit?: () => Promise<void>;
}

export interface AppOptions { db: Db; hooks?: Hooks }

declare module "fastify" {
  interface FastifyInstance { draining: boolean }
}

export function buildApp(opts: AppOptions): FastifyInstance {
  const app = Fastify({ logger: false });
  app.decorate("draining", false);

  // TODO: every error (validation, not found, conflict, unexpected) must leave as RFC 9457
  // application/problem+json (see src/problems.ts). Add an error handler.

  app.get("/readyz", async () => {
    // TODO: readiness must go false while the process drains (see src/shutdown.ts)
    return { ready: true };
  });

  app.get<{ Params: { id: string } }>("/v1/opportunities/:id", async (req, reply) => {
    const tenant = String(req.headers["x-tenant-id"] || "");
    const row = await withTenant(opts.db.db, tenant, (trx) =>
      trx.selectFrom("opportunities").selectAll().where("id", "=", Number(req.params.id)).executeTakeFirst());
    if (!row) return reply.code(404).send({ error: "not found" });
    return row;
  });

  registerTransitions(app, opts);
  return app;
}
