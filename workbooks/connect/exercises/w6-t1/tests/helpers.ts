import * as fs from "fs";
import * as path from "path";
import { LocalS3 } from "../src/s3mirror";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const cfg = JSON.parse(fs.readFileSync(path.join(root, "config/report-config.json"), "utf8"));
export const s3 = () => new LocalS3(path.join(root, "incident/s3"));
export const cid = (n: number) => `7e3b9a10-${String(n).padStart(4, "0")}-4c2d-9e8f-${String(n).padStart(12, "0")}`;
/** Luhn-valid 13-19 digit runs (spaces/dashes allowed) */
export function cardNumbersIn(text: string): string[] {
  const hits = text.match(/\b(?:\d[ -]?){12,18}\d\b/g) || [];
  return hits.filter((m) => {
    const d = m.replace(/[ -]/g, "");
    if (d.length < 13 || d.length > 19) return false;
    let s = 0;
    for (let i = 0; i < d.length; i++) { let x = d.charCodeAt(d.length - 1 - i) - 48; if (i % 2) { x *= 2; if (x > 9) x -= 9; } s += x; }
    return s % 10 === 0;
  });
}
