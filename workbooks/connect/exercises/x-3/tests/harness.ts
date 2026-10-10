// Loaders for the x-3 tests.
import * as fs from "fs";
import * as path from "path";
import { loadBot } from "../tools/nlu";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const botDir = path.join(root, "bot/HelpDeskBot");
export const bot = () => loadBot(botDir);
export const readJson = (rel: string) => JSON.parse(fs.readFileSync(path.join(botDir, rel), "utf8"));
export const cases = (file: string) =>
  fs.readFileSync(file, "utf8").trim().split("\n").slice(1).map((l) => {
    const [utterance, intent, system] = l.split(",");
    return { utterance, intent, system };
  });
export const evalCases = () => cases(path.join(root, "evals/utterances.csv"));
