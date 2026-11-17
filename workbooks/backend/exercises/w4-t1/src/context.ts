// Per-request context for the GraphQL layer.
import DataLoader from "dataloader";
import type { Auth, Account, Store } from "./store";

export interface Loaders { account: DataLoader<string, Account | null> }
export interface Context { auth: Auth; store: Store; loaders: Loaders }

// KEY-2410 (sprint 44): fix the N+1 on the pipeline view. One loader for the process, configured at
// startup, so every request shares the batching.
let store: Store;
let currentAuth: Auth;
let accountLoader: DataLoader<string, Account | null>;

export function configureLoaders(s: Store): void {
  store = s;
  accountLoader = new DataLoader<string, Account | null>((ids) => store.batchGetAccounts(currentAuth, ids));
}

export function createContext(auth: Auth, s: Store): Context {
  if (!accountLoader || store !== s) configureLoaders(s);
  currentAuth = auth;
  return { auth, store: s, loaders: { account: accountLoader } };
}
