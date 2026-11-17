// HTTP entry for the read layer: POST /graphql. Auth comes from the gateway-verified token, which the
// gateway forwards as X-Tenant-Id / X-User-Id.
import { graphql } from "graphql";
import { schema, rootValue } from "./schema";
import { createContext } from "./context";
import type { Store } from "./store";

export interface GqlRequest { headers: Record<string, string>; body: { query: string; variables?: Record<string, unknown> } }
export interface GqlResponse { status: number; headers: Record<string, string>; body: { data?: unknown; errors?: unknown[] } }

export async function handleGraphql(store: Store, req: GqlRequest): Promise<GqlResponse> {
  const tenantId = req.headers["x-tenant-id"];
  const userId = req.headers["x-user-id"];
  if (!tenantId || !userId) return { status: 401, headers: {}, body: { errors: [{ message: "unauthenticated" }] } };
  const contextValue = createContext({ tenantId, userId }, store);
  const result = await graphql({ schema, source: req.body.query, variableValues: req.body.variables, rootValue, contextValue });
  return {
    status: 200,
    headers: { "content-type": "application/json", "cache-control": "private, no-store" },
    body: JSON.parse(JSON.stringify(result)),
  };
}
