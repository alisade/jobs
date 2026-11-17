// SDP audit for the Voice Connector trunk. Implement auditSdp (see README.md, "Your task").
//
// A finding: { code, severity, line, message }
//   code      one of the codes in README.md
//   severity  "error" for what breaks media on this trunk, "warning" otherwise
//   line      1-based line number in the SDP body where the problem is
export type Finding = { code: string; severity: "error" | "warning"; line: number; message: string };

export function auditSdp(sdp: string): Finding[] {
  // TODO
  void sdp;
  return [];
}
