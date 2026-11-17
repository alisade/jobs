"use strict";
/**
 * A local fake of the ServiceNow REST surface the workbook uses. NOT ServiceNow: it models
 * the documented behavior that integration code must cope with.
 *
 *   POST /oauth_token.do                    OAuth 2.0 token endpoint (grant_type=client_credentials,
 *                                           client_id, client_secret as form fields)
 *   GET  /api/now/table/<table>             Table API list: sysparm_query, sysparm_limit,
 *                                           sysparm_offset, sysparm_fields; X-Total-Count + Link headers
 *   GET  /api/now/table/<table>/<sys_id>    Table API get
 *   POST /api/now/table/<table>             Table API create (201)
 *   PATCH /api/now/table/<table>/<sys_id>   Table API update
 *
 * Fault injection (set at start or via server.faults):
 *   rateLimit: [n, ...]        request ordinals (1-based, Table API only) that get 429 + Retry-After
 *   retryAfterSeconds          value of Retry-After (default 1)
 *   latencyMs                  added to every Table API response
 *   tokenTtlSeconds            access token lifetime (default 1800)
 *   expireTokensAfter          Table API request ordinal after which current tokens are revoked (401)
 *   createCommitThenFail: [n]  create ordinals that COMMIT the record but answer 504 (gateway timeout),
 *                              the classic duplicate-incident trap
 *   failStatus: {ordinal: status}  arbitrary failures without commit
 */
const http = require("node:http");
const crypto = require("node:crypto");

const DEFAULT_CLIENT = { clientId: "connect-integration", clientSecret: "s3cr3t-client" };

function sysId() {
  return crypto.randomBytes(16).toString("hex");
}

/** Parse the encoded-query subset: a=b^c!=d^eLIKEx^fINa,b^gISEMPTY^ORDERBYx^ORDERBYDESCy, with ^OR. */
function parseQuery(q) {
  const clauses = [];
  const order = [];
  if (!q) return { clauses, order };
  for (const raw of q.split("^")) {
    if (!raw) continue;
    let part = raw;
    let or = false;
    if (part.startsWith("OR") && !part.startsWith("ORDERBY")) {
      or = true;
      part = part.slice(2);
    }
    if (part.startsWith("ORDERBYDESC")) { order.push({ field: part.slice(11), desc: true }); continue; }
    if (part.startsWith("ORDERBY")) { order.push({ field: part.slice(7), desc: false }); continue; }
    let m;
    if ((m = /^([a-z0-9_.]+)ISEMPTY$/.exec(part))) clauses.push({ or, field: m[1], op: "ISEMPTY" });
    else if ((m = /^([a-z0-9_.]+)ISNOTEMPTY$/.exec(part))) clauses.push({ or, field: m[1], op: "ISNOTEMPTY" });
    else if ((m = /^([a-z0-9_.]+)(!=|>=|<=|=|>|<|LIKE|STARTSWITH|IN|NOT IN)(.*)$/.exec(part))) clauses.push({ or, field: m[1], op: m[2], value: m[3] });
    else throw Object.assign(new Error(`unsupported sysparm_query clause: ${raw}`), { status: 400 });
  }
  return { clauses, order };
}

function matches(rec, clauses) {
  if (!clauses.length) return true;
  // ServiceNow evaluates ^OR as binding tighter than ^ (OR groups between ANDs).
  const groups = [];
  for (const c of clauses) {
    if (c.or && groups.length) groups[groups.length - 1].push(c);
    else groups.push([c]);
  }
  return groups.every((g) => g.some((c) => test(rec, c)));
}

function test(rec, c) {
  const v = rec[c.field] == null ? "" : String(rec[c.field]);
  switch (c.op) {
    case "=": return v === c.value;
    case "!=": return v !== c.value;
    case ">": return v > c.value;
    case "<": return v < c.value;
    case ">=": return v >= c.value;
    case "<=": return v <= c.value;
    case "LIKE": return v.toLowerCase().includes(c.value.toLowerCase());
    case "STARTSWITH": return v.startsWith(c.value);
    case "IN": return c.value.split(",").includes(v);
    case "NOT IN": return !c.value.split(",").includes(v);
    case "ISEMPTY": return v === "";
    case "ISNOTEMPTY": return v !== "";
    default: return false;
  }
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

/**
 * Start the fake. Returns a promise of {url, stop, db, requests, faults, tokens, counters}.
 * opts.seed: {table: [records]} initial data; opts.client: {clientId, clientSecret}.
 */
function startFakeServiceNow(opts = {}) {
  const client = opts.client || DEFAULT_CLIENT;
  const faults = { retryAfterSeconds: 1, tokenTtlSeconds: 1800, rateLimit: [], createCommitThenFail: [], failStatus: {}, ...(opts.faults || {}) };
  const db = {};
  for (const [table, rows] of Object.entries(opts.seed || {})) db[table] = rows.map((r) => ({ sys_id: r.sys_id || sysId(), ...r }));
  const tokens = new Map();
  const requests = [];
  const counters = { table: 0, create: 0, token: 0, incidentNumber: 10000 + Math.floor((opts.numberBase || 0)) };

  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, "http://localhost");
    const body = await readBody(req);
    const entry = { method: req.method, path: url.pathname, query: Object.fromEntries(url.searchParams), headers: req.headers, body, status: 0, ts: Date.now() };
    requests.push(entry);
    const send = (status, payload, headers = {}) => {
      entry.status = status;
      res.writeHead(status, { "Content-Type": "application/json", ...headers });
      res.end(payload === undefined ? "" : JSON.stringify(payload));
    };
    try {
      if (url.pathname === "/oauth_token.do" && req.method === "POST") {
        counters.token++;
        const form = new URLSearchParams(body);
        if (form.get("grant_type") !== "client_credentials") return send(400, { error: "unsupported_grant_type" });
        if (form.get("client_id") !== client.clientId || form.get("client_secret") !== client.clientSecret) return send(401, { error: "invalid_client", error_description: "access_denied" });
        const tok = crypto.randomBytes(12).toString("hex");
        tokens.set(tok, Date.now() + faults.tokenTtlSeconds * 1000);
        return send(200, { access_token: tok, token_type: "Bearer", expires_in: faults.tokenTtlSeconds, scope: "useraccount" });
      }
      const m = /^\/api\/now\/table\/([a-z0-9_]+)(?:\/([a-f0-9]+))?$/.exec(url.pathname);
      if (!m) return send(404, { error: { message: "Invalid path", detail: url.pathname }, status: "failure" });
      counters.table++;
      const ordinal = counters.table;
      if (faults.latencyMs) await new Promise((r) => setTimeout(r, faults.latencyMs));
      const auth = req.headers.authorization || "";
      const tok = auth.startsWith("Bearer ") ? auth.slice(7) : null;
      if (faults.expireTokensAfter && ordinal > faults.expireTokensAfter) {
        tokens.clear();
        faults.expireTokensAfter = 0;
      }
      if (!tok || !tokens.has(tok) || tokens.get(tok) < Date.now()) {
        return send(401, { error: { message: "User Not Authenticated", detail: "Required to provide Auth information" }, status: "failure" });
      }
      if ((faults.rateLimit || []).includes(ordinal)) {
        return send(429, { error: { message: "Rate limit exceeded" }, status: "failure" }, { "Retry-After": String(faults.retryAfterSeconds) });
      }
      if (faults.failStatus && faults.failStatus[ordinal]) return send(faults.failStatus[ordinal], { error: { message: "Injected failure" }, status: "failure" });
      const table = m[1];
      const id = m[2];
      const rows = (db[table] = db[table] || []);
      const project = (r) => {
        const f = url.searchParams.get("sysparm_fields");
        if (!f) return r;
        return Object.fromEntries(f.split(",").map((k) => [k, r[k] === undefined ? "" : r[k]]));
      };
      if (req.method === "GET" && id) {
        const r = rows.find((x) => x.sys_id === id);
        return r ? send(200, { result: project(r) }) : send(404, { error: { message: "No Record found" }, status: "failure" });
      }
      if (req.method === "GET") {
        const { clauses, order } = parseQuery(url.searchParams.get("sysparm_query") || "");
        let hits = rows.filter((r) => matches(r, clauses));
        for (const o of order.reverse()) hits = hits.slice().sort((a, b) => (String(a[o.field]) < String(b[o.field]) ? -1 : String(a[o.field]) > String(b[o.field]) ? 1 : 0) * (o.desc ? -1 : 1));
        const limit = Math.min(Number(url.searchParams.get("sysparm_limit") || 10000), 10000);
        const offset = Number(url.searchParams.get("sysparm_offset") || 0);
        const page = hits.slice(offset, offset + limit);
        const headers = { "X-Total-Count": String(hits.length) };
        if (offset + limit < hits.length) {
          const next = new URL(url.toString());
          next.searchParams.set("sysparm_offset", String(offset + limit));
          headers.Link = `<${next.pathname}${next.search}>;rel="next"`;
        }
        return send(200, { result: page.map(project) }, headers);
      }
      if (req.method === "POST") {
        counters.create++;
        let rec;
        try {
          rec = JSON.parse(body || "{}");
        } catch {
          return send(400, { error: { message: "Exception while reading request", detail: "invalid JSON" }, status: "failure" });
        }
        const now = new Date().toISOString().replace("T", " ").slice(0, 19);
        const created = { ...rec, sys_id: sysId(), sys_created_on: now, sys_updated_on: now };
        if (table === "incident") created.number = `INC${String(++counters.incidentNumber).padStart(7, "0")}`;
        if (table === "sn_customerservice_case" || table === "task") created.number = `TASK${String(++counters.incidentNumber).padStart(7, "0")}`;
        rows.push(created);
        if ((faults.createCommitThenFail || []).includes(counters.create)) {
          return send(504, { error: { message: "Gateway Timeout" }, status: "failure" });
        }
        return send(201, { result: project(created) }, { Location: `/api/now/table/${table}/${created.sys_id}` });
      }
      if (req.method === "PATCH" || req.method === "PUT") {
        const r = rows.find((x) => x.sys_id === id);
        if (!r) return send(404, { error: { message: "No Record found" }, status: "failure" });
        Object.assign(r, JSON.parse(body || "{}"));
        return send(200, { result: project(r) });
      }
      return send(405, { error: { message: "Method not allowed" }, status: "failure" });
    } catch (err) {
      return send(err.status || 500, { error: { message: String(err.message) }, status: "failure" });
    }
  });

  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({
        url: `http://127.0.0.1:${port}`,
        client,
        db,
        requests,
        faults,
        tokens,
        counters,
        tableRequests: () => requests.filter((r) => r.path.startsWith("/api/now/table/")),
        stop: () => new Promise((r) => server.close(() => r())),
      });
    });
  });
}

module.exports = { startFakeServiceNow, parseQuery, DEFAULT_CLIENT };
