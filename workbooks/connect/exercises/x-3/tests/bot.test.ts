// Visible tests for connect/x-3. The grader adds more.
import * as fs from "fs";
import * as path from "path";
import { recognize } from "../tools/nlu";
import { bot, botDir, readJson } from "./harness";

test("the export is a loadable Lex V2 JSON export (manifest, bot, locale, slot types referenced by slots exist)", () => {
  expect(JSON.parse(fs.readFileSync(path.join(botDir, "..", "manifest.json"), "utf8")).metadata.fileFormat).toBe("LexJson");
  const b = bot();
  for (const i of b.intents) for (const t of Object.values(i.slots)) expect(b.slotTypes[t]).toBeDefined();
  expect(readJson("BotLocales/en_US/BotLocale.json").identifier).toBe("en_US");
});

test("intents without slots still work", () => {
  const b = bot();
  expect(recognize(b, "check my ticket").intent).toBe("CheckTicketStatus");
  expect(recognize(b, "there is an outage").intent).toBe("ReportOutage");
  expect(recognize(b, "i forgot my password").intent).toBe("ResetPassword");
});
