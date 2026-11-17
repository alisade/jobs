// Per-request context for the GraphQL layer.
// Loaders are created per request: a DataLoader's cache is a per-request memo, and its batch function
// must run with the identity of the request that asked. A process-wide loader shares cached rows across
// users and tenants (ids are only unique per tenant) and batches one request's ids under another
// request's auth.
import DataLoader from "dataloader";
import type { Auth, Account, Store } from "./store";

export interface Loaders { account: DataLoader<string, Account | null> }
export interface Context { auth: Auth; store: Store; loaders: Loaders }

export function createLoaders(store: Store, auth: Auth): Loaders {
  return {
    account: new DataLoader<string, Account | null>((ids) => store.batchGetAccounts(auth, ids)),
  };
}

// Kept for callers of the old API; nothing to configure any more.
export function configureLoaders(_s: Store): void { /* loaders are per request now */ }

export function createContext(auth: Auth, store: Store): Context {
  return { auth, store, loaders: createLoaders(store, auth) };
}
