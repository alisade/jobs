import * as fs from "fs";
import * as path from "path";
import { openDb } from "bk-kit";

const ROOT = path.resolve(__dirname, "..");
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { migrate } = require("../scripts/migrate");
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { lintDir } = require("../scripts/lint");

test("all migrations apply on a seeded database", async () => {
  const db = await openDb();
  await migrate(db, { seedSql: fs.readFileSync(path.join(ROOT, "scripts", "seed.sql"), "utf8") });
  const r = await db.query<{ n: number }>("SELECT count(*)::int AS n FROM activities");
  expect(r.rows[0].n).toBe(40000);
  await db.close();
});

test("kmigrate-lint reports no errors", () => {
  const errors = lintDir(path.join(ROOT, "migrations")).filter((r: { level: string }) => r.level === "error");
  expect(errors).toEqual([]);
});
