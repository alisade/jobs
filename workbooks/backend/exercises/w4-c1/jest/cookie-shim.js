"use strict";
// Jest cannot require() the ESM-only `cookie` 2.x that fastify.inject (light-my-request) loads, so the
// tests map `cookie` to this small CommonJS stand-in. Only what light-my-request uses is provided.
function stringifySetCookie(c) {
  let s = `${c.name}=${encodeURIComponent(c.value == null ? "" : c.value)}`;
  if (c.path) s += `; Path=${c.path}`;
  if (c.domain) s += `; Domain=${c.domain}`;
  if (c.maxAge != null) s += `; Max-Age=${c.maxAge}`;
  if (c.expires) s += `; Expires=${new Date(c.expires).toUTCString()}`;
  if (c.httpOnly) s += "; HttpOnly";
  if (c.secure) s += "; Secure";
  if (c.sameSite) s += `; SameSite=${c.sameSite}`;
  return s;
}
function parseCookie(str) {
  const out = {};
  for (const part of String(str || "").split(";")) {
    const i = part.indexOf("=");
    if (i > 0) out[part.slice(0, i).trim()] = decodeURIComponent(part.slice(i + 1).trim());
  }
  return out;
}
module.exports = { stringifySetCookie, parseCookie, parse: parseCookie, serialize: (n, v) => stringifySetCookie({ name: n, value: v }) };
