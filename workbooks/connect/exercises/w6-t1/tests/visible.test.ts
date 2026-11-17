// Visible tests for connect/w6-t1. Run `make setup` first (the tests read incident/s3).
import { buildReport, toCsv } from "../src/report";
import { cfg, s3, cid } from "./helpers";

test("the September re-run lists every analysed contact once", () => {
  const rows = buildReport(s3(), cfg, "2026-09-20", "2026-10-07");
  expect(rows.map((r) => r.contact_id)).toEqual(Array.from({ length: 12 }, (_, i) => cid(i + 1)));
});

test("the report Finance receives contains none of the card numbers callers read out", () => {
  const csv = toCsv(buildReport(s3(), cfg, "2026-09-20", "2026-10-07"));
  for (const pan of ["4111 1111 1111 1111", "5500 0000 0000 0004", "3782 822463 10005"]) expect(csv).not.toContain(pan);
});
