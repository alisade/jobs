// GraphQL read layer for the pipeline view (Keystone web app and the agent assistant use it).
import { buildSchema } from "graphql";
import type { Context } from "./context";
import type { Opportunity } from "./store";

export const schema = buildSchema(`
  type Account { id: ID!, name: String!, ownerId: ID! }
  type Opportunity { id: ID!, name: String!, stage: String!, amount: Float!, account: Account }
  type Query { pipeline(ownerId: ID): [Opportunity!]! }
`);

// Root value resolvers (buildSchema style). Field resolvers for Opportunity.account live on the object.
export const rootValue = {
  pipeline: async (args: { ownerId?: string }, ctx: Context) => {
    const opps = await ctx.store.listOpportunities(ctx.auth, args.ownerId);
    return opps.map((o: Opportunity) => ({
      ...o,
      // KEY-2410: batched through DataLoader instead of one accounts-svc call per row (was N+1).
      account: () => ctx.loaders.account.load(o.accountId),
    }));
  },
};
