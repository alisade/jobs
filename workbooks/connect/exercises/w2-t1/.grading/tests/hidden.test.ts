// Hidden checks for connect/w2-t1.
import * as crypto from "crypto";
import * as fs from "fs";
import * as path from "path";

const root = path.resolve(__dirname, "../..");
const s = require(path.join(root, "tools/scenario"));
const profiles = require(path.join(root, "config/routing-profiles.json"));
const users = require(path.join(root, "config/users.json"));
const desk = profiles.RoutingProfiles.find((p: any) => p.Name === "rp-service-desk");
const cfgFor = (p: any, q: string) => p.QueueConfigs.find((c: any) => c.QueueReference.QueueId === q && c.QueueReference.Channel === "VOICE");

describe("environment untouched", () => {
  test("tools/ is the shipped routing model", () => {
    const want: Record<string, string> = {
      "routing-model.js": "4019225c18c911507f9c7b8832856462c38ac5bef4f705269062b5eff7798c79",
      "stream.js": "c9426914d53e506e8d279e99134c8c3853689b2b72d2f45154a245cfb3b385e4",
      "scenario.js": "0e436200c8e41f5925ee7a45ed4aaadc5f6fe63b5d6cf33ab9205f0ffbc38ec6",
    };
    for (const [f, h] of Object.entries(want)) {
      expect([f, crypto.createHash("sha256").update(fs.readFileSync(path.join(root, "tools", f))).digest("hex")]).toEqual([f, h]);
    }
  });
});

describe("the fix", () => {
  test("PasswordReset has no delay in rp-service-desk", () => {
    expect(Number(cfgFor(desk, "q-password-reset").Delay)).toBe(0);
  });
  test("week replay: GeneralSupport >= 80% and Applications >= 85%", () => {
    const w = s.replayWeek(profiles, users, "after");
    expect(w["q-general"].serviceLevel).toBeGreaterThanOrEqual(0.8);
    expect(w["q-apps"].serviceLevel).toBeGreaterThanOrEqual(0.85);
  });
  test("week replay: PasswordReset abandon rate <= 8% and ASA <= 12 s", () => {
    const w = s.replayWeek(profiles, users, "after");
    expect(w["q-password-reset"].abandonRate).toBeLessThanOrEqual(0.08);
    expect(w["q-password-reset"].asaSeconds).toBeLessThanOrEqual(12);
  });
  test("even the training day (2026-10-07) gets PasswordReset back above 72% (it was 60%)", () => {
    const r = s.replayDay(profiles, users, s.DAYS.find((d: any) => d.date === "2026-10-07"));
    expect(r.queues["q-password-reset"].serviceLevel).toBeGreaterThanOrEqual(0.72);
  });
});

describe("the consolidation is kept (fix forward, not a rollback)", () => {
  test("all 26 tier 1 and general agents stay on rp-service-desk", () => {
    const onDesk = users.Users.filter((u: any) => u.RoutingProfileName === "rp-service-desk").map((u: any) => u.Username);
    expect(onDesk.length).toBe(26);
    expect(users.Users.length).toBe(34);
  });
  test("rp-service-desk still serves all three queues", () => {
    for (const q of ["q-password-reset", "q-general", "q-apps"]) expect(cfgFor(desk, q)).toBeTruthy();
  });
  test("rp-apps and media concurrency are unchanged", () => {
    const apps = profiles.RoutingProfiles.find((p: any) => p.Name === "rp-apps");
    expect(apps.QueueConfigs.map((c: any) => [c.QueueReference.QueueId, c.Priority, c.Delay])).toEqual([["q-apps", 1, 0], ["q-general", 2, 45]]);
    expect(desk.MediaConcurrencies).toEqual([{ Channel: "VOICE", Concurrency: 1 }, { Channel: "CHAT", Concurrency: 2 }]);
  });
  test("every profile is valid: unique queue per channel, integer priority >= 1, delay >= 0", () => {
    for (const p of profiles.RoutingProfiles) {
      const keys = p.QueueConfigs.map((c: any) => `${c.QueueReference.QueueId}/${c.QueueReference.Channel}`);
      expect(new Set(keys).size).toBe(keys.length);
      for (const c of p.QueueConfigs) {
        expect(Number.isInteger(c.Priority) && c.Priority >= 1).toBe(true);
        expect(Number.isInteger(c.Delay) && c.Delay >= 0).toBe(true);
      }
    }
  });
});
