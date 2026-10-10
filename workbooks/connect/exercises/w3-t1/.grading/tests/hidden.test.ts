// Hidden tests for connect/w3-t1 (run from tests/__hidden__).
import * as fs from "fs";
import * as path from "path";
import { auditSdp } from "../../src/sdp-audit";
import { loadSbc, buildSdp, parseConf } from "../../src/sbc-sim";
import { replay } from "../../src/replay";

const root = path.resolve(__dirname, "../..");
const base = [
  "v=0", "o=SBCE 1 1 IN IP4 198.51.100.10", "s=-", "c=IN IP4 198.51.100.10", "t=0 0",
  "m=audio 35010 RTP/SAVP 0 8 127", "a=rtpmap:0 PCMU/8000", "a=rtpmap:8 PCMA/8000", "a=rtpmap:127 telephone-event/8000",
  "a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:WVNfX19zZW1jdGwgKCkgewkyMjA7fQp9CnVubGVz", "a=sendrecv",
].join("\r\n") + "\r\n";
const codes = (sdp: string) => auditSdp(sdp).map((f) => `${f.code}:${f.severity}:${f.line}`).sort();

describe("auditSdp", () => {
  test("plain RTP on the encrypted trunk is NOT_SRTP on the m= line", () => {
    expect(codes(base.replace("RTP/SAVP", "RTP/AVP").replace(/a=crypto[^\r]*\r\n/, ""))).toEqual(["NOT_SRTP:error:6"]);
  });
  test("RTP/SAVP without a=crypto is MISSING_CRYPTO", () => {
    expect(codes(base.replace(/a=crypto[^\r]*\r\n/, ""))).toEqual(["MISSING_CRYPTO:error:6"]);
  });
  test("no telephone-event is only a warning", () => {
    expect(codes(base.replace("a=rtpmap:127 telephone-event/8000\r\n", ""))).toEqual(["NO_TELEPHONE_EVENT:warning:6"]);
  });
  test("a media-level private c= is caught too", () => {
    const s = base.replace("a=sendrecv", "c=IN IP4 192.168.40.7\r\na=sendrecv");
    expect(codes(s)).toEqual(["PRIVATE_CONNECTION_ADDRESS:error:11"]);
  });
  test("RFC 1918 boundaries and CGNAT: 172.16-31 and 100.64/10 are private, 172.32 and 100.128 are not", () => {
    expect(codes(base.replace("198.51.100.10\r\nt", "172.31.0.9\r\nt"))).toEqual(["PRIVATE_CONNECTION_ADDRESS:error:4"]);
    expect(codes(base.replace("198.51.100.10\r\nt", "100.72.1.1\r\nt"))).toEqual(["PRIVATE_CONNECTION_ADDRESS:error:4"]);
    expect(codes(base.replace("198.51.100.10\r\nt", "172.32.0.9\r\nt"))).toEqual([]);
    expect(codes(base.replace("198.51.100.10\r\nt", "100.128.0.1\r\nt"))).toEqual([]);
  });
  test("LF-only line endings are accepted", () => {
    expect(codes(base.replace(/\r\n/g, "\n").replace("c=IN IP4 198.51.100.10", "c=IN IP4 10.1.1.1"))).toEqual(["PRIVATE_CONNECTION_ADDRESS:error:4"]);
  });
  test("no connection address anywhere is MISSING_CONNECTION", () => {
    expect(codes(base.replace("c=IN IP4 198.51.100.10\r\n", ""))).toEqual(["MISSING_CONNECTION:error:5"]);
  });
  test("over the incident bundle it flags exactly the SBCE-B SDPs of the three dead-air calls", () => {
    const recs = fs.readFileSync(path.join(root, "incident/vc-sip-messages.jsonl"), "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
    const flagged = new Set<string>();
    for (const r of recs) {
      const i = r.sip_message.indexOf("\r\n\r\n");
      const body = r.sip_message.slice(i + 4);
      if (body.trim() && auditSdp(body).some((f) => f.code === "PRIVATE_CONNECTION_ADDRESS")) flagged.add(r.call_id);
    }
    expect([...flagged].sort()).toEqual(["0c8e5b71d2a94f6e8b3a1d9c7e5f2a40", "9b7d5f3e1c2a4b6d8f0e1a3c5e7b9d01", "c2a4e6f8b0d24c1e9f7a5b3d1c0e8a26"]);
  });
});

describe("fixed trunk", () => {
  test("SBCE-B advertises its NAT address 198.51.100.11 for media", () => {
    const sdp = buildSdp(loadSbc("ashburn-sbce-b"), { sessionId: "1", port: 35000 });
    expect(/^c=IN IP4 (\S+)/m.exec(sdp)![1]).toBe("198.51.100.11");
  });
  test("a day of replayed traffic has no one-way calls", () => {
    expect(replay(200).oneWay).toBe(0);
  });
  test("guard: SBCE-A and the Dallas DR profile are unchanged", () => {
    const a = parseConf(fs.readFileSync(path.join(root, "config/sbc/ashburn-sbce-a.conf"), "utf8"));
    const d = parseConf(fs.readFileSync(path.join(root, "config/sbc/dallas-sbce-dr.conf"), "utf8"));
    expect(a["media-interface trunk-vc-media"]).toEqual({ ip: "10.20.4.21", "public-ip": "198.51.100.10", "rtp-port-range": "35000-40000" });
    expect(d["media-interface trunk-vc-media"]).toEqual({ ip: "10.40.4.21", "public-ip": "203.0.113.20", "rtp-port-range": "35000-40000" });
  });
  test("guard: SDP settings (SRTP, codecs, telephone-event 127) are unchanged on every SBCE", () => {
    for (const n of ["ashburn-sbce-a", "ashburn-sbce-b", "dallas-sbce-dr"]) {
      expect(loadSbc(n).sdp).toEqual({ profile: "RTP/SAVP", "crypto-suite": "AES_CM_128_HMAC_SHA1_80", "codec-order": "PCMU,PCMA", "telephone-event-pt": "127", ptime: "20" });
    }
  });
});
