// SDP audit for the Voice Connector trunk (reference implementation).
export type Finding = { code: string; severity: "error" | "warning"; line: number; message: string };

function isPrivateV4(ip: string): boolean {
  const p = ip.split(".").map(Number);
  if (p.length !== 4 || p.some((x) => !Number.isInteger(x))) return false;
  const [a, b] = p;
  return a === 10 || a === 127 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || (a === 100 && b >= 64 && b <= 127) || (a === 169 && b === 254);
}

export function auditSdp(sdp: string): Finding[] {
  const lines = sdp.split(/\r?\n/);
  const out: Finding[] = [];
  let sessionC: number | null = null;
  type M = { line: number; profile: string; hasC: boolean; crypto: boolean; te: boolean };
  const media: M[] = [];
  lines.forEach((l, i) => {
    const n = i + 1;
    const c = /^c=IN IP4 (\S+)/.exec(l);
    if (c) {
      if (media.length) media[media.length - 1].hasC = true; else sessionC = n;
      if (isPrivateV4(c[1])) {
        out.push({ code: "PRIVATE_CONNECTION_ADDRESS", severity: "error", line: n, message: `connection address ${c[1]} is not publicly routable: the far end will send RTP nowhere (one-way audio)` });
      }
    }
    const m = /^m=audio \d+ (\S+)/.exec(l);
    if (m) media.push({ line: n, profile: m[1], hasC: false, crypto: false, te: false });
    if (media.length && /^a=crypto:/.test(l)) media[media.length - 1].crypto = true;
    if (media.length && /^a=rtpmap:\d+ telephone-event\//i.test(l)) media[media.length - 1].te = true;
  });
  for (const m of media) {
    if (!m.hasC && sessionC === null) out.push({ code: "MISSING_CONNECTION", severity: "error", line: m.line, message: "no c= line at session or media level" });
    if (m.profile === "RTP/AVP") out.push({ code: "NOT_SRTP", severity: "error", line: m.line, message: "plain RTP offered on an encrypted trunk (expected RTP/SAVP)" });
    if (m.profile === "RTP/SAVP" && !m.crypto) out.push({ code: "MISSING_CRYPTO", severity: "error", line: m.line, message: "RTP/SAVP without a=crypto: no SDES keys to set up SRTP" });
    if (!m.te) out.push({ code: "NO_TELEPHONE_EVENT", severity: "warning", line: m.line, message: "no telephone-event payload: RFC 4733 DTMF not offered" });
  }
  return out;
}
