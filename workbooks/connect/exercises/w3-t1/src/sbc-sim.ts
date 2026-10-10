// Stand-in for the SBC's SDP builder and for the media path to Voice Connector. Works as shipped:
// it reads config/sbc/*.conf exactly the way the SBCE profile does (simplified) and renders the
// SDP the SBC would put in an INVITE (offer) or a 200 OK (answer).
import * as fs from "fs";
import * as path from "path";

export type SbcConfig = Record<string, Record<string, string>>;

export function parseConf(text: string): SbcConfig {
  const out: SbcConfig = {};
  let section = "";
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.replace(/#.*$/, "").trim();
    if (!line) continue;
    const m = /^\[(.+)\]$/.exec(line);
    if (m) { section = m[1]; out[section] = out[section] || {}; continue; }
    const kv = /^([^=]+?)\s*=\s*(.*)$/.exec(line);
    if (kv && section) out[section][kv[1]] = kv[2];
  }
  return out;
}

export const confDir = path.resolve(__dirname, "../config/sbc");
export function loadSbc(name: string, dir = confDir): SbcConfig {
  return parseConf(fs.readFileSync(path.join(dir, `${name}.conf`), "utf8"));
}
export const SBCS = ["ashburn-sbce-a", "ashburn-sbce-b", "dallas-sbce-dr"];

const PT: Record<string, number> = { PCMU: 0, PCMA: 8 };

/** The SDP body this SBC sends toward Voice Connector. */
export function buildSdp(cfg: SbcConfig, opts: { sessionId: string; port: number; key?: string }): string {
  const media = cfg["media-interface trunk-vc-media"] || {};
  const sdp = cfg.sdp || {};
  const addr = media["public-ip"] || media.ip; // the SBCE advertises the public (NAT) address only when configured
  const sig = cfg["signaling-interface trunk-vc"] || {};
  const codecs = (sdp["codec-order"] || "PCMU").split(",").map((c) => c.trim());
  const te = sdp["telephone-event-pt"] || "101";
  const pts = [...codecs.map((c) => PT[c]), te].join(" ");
  const lines = [
    "v=0",
    `o=SBCE ${opts.sessionId} 1 IN IP4 ${sig["public-ip"] || sig.ip}`,
    "s=-",
    `c=IN IP4 ${addr}`,
    "t=0 0",
    `m=audio ${opts.port} ${sdp.profile || "RTP/AVP"} ${pts}`,
    ...codecs.map((c) => `a=rtpmap:${PT[c]} ${c}/8000`),
    `a=rtpmap:${te} telephone-event/8000`,
    `a=fmtp:${te} 0-15`,
    `a=ptime:${sdp.ptime || "20"}`,
  ];
  if ((sdp.profile || "").includes("SAVP")) lines.push(`a=crypto:1 ${sdp["crypto-suite"]} inline:${opts.key || "WVNfX19zZW1jdGwgKCkgewkyMjA7fQp9CnVubGVz"}`);
  lines.push("a=sendrecv");
  return lines.join("\r\n") + "\r\n";
}
