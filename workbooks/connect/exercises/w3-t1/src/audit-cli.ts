// make audit: run auditSdp over every SDP body in incident/vc-sip-messages.jsonl and print one
// line per finding with the call id and SIP message. Works as shipped once auditSdp works.
import * as fs from "fs";
import * as path from "path";
import { auditSdp } from "./sdp-audit";

const file = path.resolve(__dirname, "../incident/vc-sip-messages.jsonl");
if (!fs.existsSync(file)) { console.error("run make setup first (incident/ bundle missing)"); process.exit(2); }
let n = 0;
for (const line of fs.readFileSync(file, "utf8").split("\n").filter(Boolean)) {
  const rec = JSON.parse(line);
  const msg: string = rec.sip_message;
  const split = msg.indexOf("\r\n\r\n");
  const body = split >= 0 ? msg.slice(split + 4) : "";
  if (!body.trim()) continue;
  const first = msg.split("\r\n")[0];
  for (const f of auditSdp(body)) {
    n++;
    console.log(`${rec.event_timestamp}  ${rec.call_id.slice(0, 18).padEnd(18)}  ${first.slice(0, 40).padEnd(40)}  ${f.severity.padEnd(7)} ${f.code.padEnd(28)} line ${f.line}: ${f.message}`);
  }
}
console.log(`${n} finding(s)`);
