// Visible checks for connect/w2-t1: the routing profiles in config/ replayed over the week of 2026-10-05.
import * as path from "path";

const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
const s = require(path.join(root, "tools/scenario"));
const profiles = require(path.join(root, "config/routing-profiles.json"));
const users = require(path.join(root, "config/users.json"));

test("config/ still maps onto the routing model", () => {
  expect(() => s.toModel(profiles, users, s.DAYS[5])).not.toThrow();
});

test("PasswordReset weekly service level is back at or above 82% (30 s)", () => {
  const w = s.replayWeek(profiles, users, "after");
  expect(w["q-password-reset"].serviceLevel).toBeGreaterThanOrEqual(0.82);
});
