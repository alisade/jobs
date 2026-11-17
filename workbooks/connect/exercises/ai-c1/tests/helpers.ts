// Shared helpers for the ai-c1 tests.
import * as path from "path";
import { replayClient, loadCases } from "../src/replay";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const cases = loadCases(root);
export const transcriptOf = (id: string) => cases.find((c) => c.id === id)!.transcript;
export const replay = (opts: { delayMs?: number } = {}) => replayClient(root, opts);
