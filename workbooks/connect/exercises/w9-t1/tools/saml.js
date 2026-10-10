"use strict";
// Small SAML helpers for the investigation (provided).
//   node tools/saml.js decode <file-with-base64-SAMLResponse>   print the assertion XML
//   node tools/saml.js attrs                                    evaluate the Okta attribute statements for users-sample.csv
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");

/** Evaluate the tiny subset of Okta Expression Language used in this app. */
function evalOktaExpr(expr, user) {
  const e = String(expr).trim();
  let m;
  if ((m = /^String\.substringBefore\((.+),\s*"(.*)"\)$/.exec(e))) {
    const v = evalOktaExpr(m[1], user);
    const i = v.indexOf(m[2]);
    return i < 0 ? v : v.slice(0, i);
  }
  if ((m = /^String\.toLowerCase\((.+)\)$/.exec(e))) return evalOktaExpr(m[1], user).toLowerCase();
  if ((m = /^user\.(\w+)$/.exec(e))) return String(user[m[1]] ?? "");
  if ((m = /^"(.*)"$/.exec(e))) return m[1];
  return e; // literal value (e.g. role ARNs, durations)
}

function readUsers(root = ROOT) {
  const [head, ...rows] = fs.readFileSync(path.join(root, "config/users-sample.csv"), "utf8").trim().split(/\r?\n/);
  const cols = head.split(",");
  return rows.map((r) => Object.fromEntries(r.split(",").map((v, i) => [cols[i], v])));
}

function decode(b64) {
  return Buffer.from(String(b64).trim(), "base64").toString("utf8");
}

if (require.main === module) {
  const [cmd, arg] = process.argv.slice(2);
  if (cmd === "decode") {
    const raw = fs.readFileSync(arg, "utf8");
    const m = /SAMLResponse=([A-Za-z0-9+/=%]+)/.exec(raw);
    console.log(decode(decodeURIComponent(m ? m[1] : raw)));
  } else if (cmd === "attrs") {
    const app = JSON.parse(fs.readFileSync(path.join(ROOT, "idp/okta-connect-app.json"), "utf8"));
    for (const u of readUsers()) {
      const user = { email: u.Email, login: u.Email, firstName: u.FirstName, lastName: u.LastName };
      const out = app.settings.signOn.attributeStatements.map((a) => `${a.name.split("/").pop()}=${evalOktaExpr(a.values[0], user)}`);
      console.log(`${u.Username.padEnd(12)} ${out.join("  ")}`);
    }
  } else {
    console.log("usage: node tools/saml.js decode <file> | attrs");
  }
}

module.exports = { evalOktaExpr, readUsers, decode };
