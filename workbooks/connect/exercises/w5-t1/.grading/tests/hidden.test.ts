// Hidden checks for connect/w5-t1 (run from tests/__hidden__).
import { ask, callers, forbidden, schema, traffic } from "../harness";
import { exportAll } from "../../src/exporter";
import { buildFilter } from "../../src/retriever";
import { loadArticles } from "../../src/kbsim";

const keysOf = (f: any): string[] => (f.andAll || f.orAll ? (f.andAll || f.orAll).flatMap(keysOf) : [Object.values(f)[0] as any].map((x: any) => x.key));

describe("exporter contract", () => {
  const objs = exportAll(loadArticles());
  test("every sidecar carries exactly the schema attributes", () => {
    const want = Object.keys(schema.attributes).sort();
    for (const o of objs) expect(Object.keys(o.sidecar.metadataAttributes).sort()).toEqual(want);
  });
  test("department is carried under the key consumers filter on", () => {
    const fin = objs.find((o) => o.sidecar.metadataAttributes.articleId === "KB0020456")!;
    expect(fin.sidecar.metadataAttributes.department).toBe("Finance");
    expect((fin.sidecar.metadataAttributes as any).dept).toBeUndefined();
  });
  test("retired articles keep status retired (filterable), drafts are not exported", () => {
    const old = objs.find((o) => o.sidecar.metadataAttributes.articleId === "KB0009001")!;
    expect(old.sidecar.metadataAttributes.status).toBe("retired");
    expect(exportAll([{ ...loadArticles()[0], number: "KB0099999", workflow_state: "draft" }]).length).toBe(0);
  });
  test("region is normalized to lower case", () => {
    for (const o of objs) expect(o.sidecar.metadataAttributes.region).toBe(o.sidecar.metadataAttributes.region.toLowerCase());
  });
});

describe("retriever contract", () => {
  test("every filter key exists in the KB metadata schema", () => {
    for (const who of Object.values(callers)) for (const k of keysOf(buildFilter(who))) expect(Object.keys(schema.attributes)).toContain(k);
  });
  test("an empty filtered result hands off (no second, unfiltered call)", async () => {
    for (const [c, q] of [["anon", "how do I re-enroll my vpn token"], ["ctr-in", "map the finance drive"], ["it-in", "change my bank account for payroll"]]) {
      const { calls, r } = await ask(c, q);
      expect(calls.length).toBe(1);
      expect(calls[0].retrievalConfiguration.vectorSearchConfiguration.filter).toBeDefined();
      expect(r.status).toBe("NO_ARTICLES");
    }
  });
  test("the retrieval log no longer reports an unfiltered fallback", async () => {
    for (const t of traffic.traffic) {
      const { r } = await ask(t.caller, t.query);
      expect(r.log.fallback ?? null).toBeNull();
    }
  });
});

describe("replay after the fix", () => {
  test("no forbidden article in any replayed contact", async () => {
    for (const t of traffic.traffic) {
      const { r } = await ask(t.caller, t.query);
      for (const x of r.results) expect(forbidden(callers[t.caller], x.metadata)).toBe(false);
    }
  });
  test("the retired RSA article is never served; Finance gets its drive article instead", async () => {
    const { ids } = await ask("fin-uk", "rsa token for my finance laptop");
    expect(ids).not.toContain("KB0009001");
    expect(ids).toContain("KB0020456");
  });
  test("HR finds the HR-only payroll article", async () => {
    expect((await ask("hr-us", "change my bank account for payroll")).ids[0]).toBe("KB0030001");
  });
  test("Legal finds the legal hold article (not a random low-score one)", async () => {
    expect((await ask("legal-us", "legal hold on my mailbox")).ids[0]).toBe("KB0040001");
  });
  test("Finance in the US finds the SAP posting period article", async () => {
    expect((await ask("fin-us", "sap posting period for quarter end")).ids[0]).toBe("KB0020457");
  });
  test("a contractor gets the contractor MFA article and never employee-only ones", async () => {
    const { ids } = await ask("ctr-in", "enroll my new phone for mfa");
    expect(ids).toEqual(expect.arrayContaining(["KB0031002", "KB0031003"]));
  });
  test("an unverified caller asking about VPN tokens gets nothing", async () => {
    expect((await ask("anon", "how do I re-enroll my vpn token")).r.status).toBe("NO_ARTICLES");
  });
});
