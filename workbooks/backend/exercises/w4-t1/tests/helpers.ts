import { handleGraphql } from "../src/server";
import type { Store } from "../src/store";

export const PIPELINE = `query Pipeline($owner: ID) { pipeline(ownerId: $owner) { id name stage account { id name } } }`;

export async function pipeline(store: Store, tenantId: string, userId: string, owner?: string) {
  const res = await handleGraphql(store, { headers: { "x-tenant-id": tenantId, "x-user-id": userId }, body: { query: PIPELINE, variables: { owner } } });
  if (res.body.errors) throw new Error(JSON.stringify(res.body.errors));
  return (res.body.data as { pipeline: { id: string; name: string; account: { id: string; name: string } | null }[] }).pipeline;
}

export const accountNames = (rows: { account: { name: string } | null }[]) => rows.map((r) => (r.account ? r.account.name : null));
