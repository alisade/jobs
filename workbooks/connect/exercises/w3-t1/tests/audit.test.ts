// Visible tests for connect/w3-t1. The grader adds more (all finding codes, the bundle, replay,
// and guards against unrelated changes).
import { auditSdp } from "../src/sdp-audit";
import { SBCS, loadSbc, buildSdp } from "../src/sbc-sim";

const vcAnswer = [
  "v=0", "o=- 4410 1 IN IP4 3.80.16.42", "s=-", "c=IN IP4 3.80.16.42", "t=0 0",
  "m=audio 17020 RTP/SAVP 0 101", "a=rtpmap:0 PCMU/8000", "a=rtpmap:101 telephone-event/8000",
  "a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo3NjU0", "a=sendrecv",
].join("\r\n") + "\r\n";

test("a clean Voice Connector answer has no findings", () => {
  expect(auditSdp(vcAnswer)).toEqual([]);
});

test("a private connection address is an error on the c= line", () => {
  const f = auditSdp(vcAnswer.replace("c=IN IP4 3.80.16.42", "c=IN IP4 10.20.8.15"));
  expect(f).toEqual([expect.objectContaining({ code: "PRIVATE_CONNECTION_ADDRESS", severity: "error", line: 4 })]);
});

test("every SBCE on the trunk advertises a publicly routable media address", () => {
  for (const name of SBCS.concat("dallas-sbce-dr")) {
    const sdp = buildSdp(loadSbc(name), { sessionId: "1", port: 35000 });
    const errs = auditSdp(sdp).filter((x) => x.severity === "error");
    expect({ name, errs }).toEqual({ name, errs: [] });
  }
});
