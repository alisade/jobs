// Replays a day of trunk traffic through the CURRENT config/sbc/*.conf: picks the SBC for each
// call the way Voice Connector origination does (priority 1 routes, 50/50 weight), renders the
// SBC's SDP and follows the media: RTP from Voice Connector goes to the SDP connection address.
// Works as shipped; run with `make replay` after your fix.
import { SBCS, loadSbc, buildSdp } from "./sbc-sim";

export type CallResult = { call: number; sbc: string; connection: string; lfgHearsFarEnd: boolean; farEndHearsLfg: boolean };

const isPrivate = (ip: string) => {
  const [a, b] = ip.split(".").map(Number);
  return a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || (a === 100 && b >= 64 && b <= 127);
};

export function replay(calls = 200, dir?: string): { results: CallResult[]; oneWay: number } {
  let seed = 20261008;
  const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
  const results: CallResult[] = [];
  for (let i = 0; i < calls; i++) {
    const sbc = rnd() < 0.5 ? SBCS[0] : SBCS[1]; // Dallas (priority 2) only takes calls when both Ashburn SBCEs are down
    const sdp = buildSdp(loadSbc(sbc, dir), { sessionId: String(1000 + i), port: 35000 + 2 * (i % 2500) });
    const connection = /^c=IN IP4 (\S+)/m.exec(sdp)![1];
    const toLfg = !isPrivate(connection); // VC -> SBC RTP is sent to the advertised address
    results.push({ call: i + 1, sbc, connection, lfgHearsFarEnd: toLfg, farEndHearsLfg: true });
  }
  return { results, oneWay: results.filter((r) => !r.lfgHearsFarEnd || !r.farEndHearsLfg).length };
}

if (require.main === module || process.env.RUN_TS_MAIN === __filename) {
  const { results, oneWay } = replay();
  const by: Record<string, { calls: number; oneWay: number }> = {};
  for (const r of results) {
    by[r.sbc] = by[r.sbc] || { calls: 0, oneWay: 0 };
    by[r.sbc].calls++;
    if (!r.lfgHearsFarEnd || !r.farEndHearsLfg) by[r.sbc].oneWay++;
  }
  console.log("sbc                calls  one-way");
  for (const [k, v] of Object.entries(by)) console.log(`${k.padEnd(18)} ${String(v.calls).padStart(5)}  ${String(v.oneWay).padStart(7)}`);
  console.log(`total one-way calls: ${oneWay} / ${results.length}`);
}
