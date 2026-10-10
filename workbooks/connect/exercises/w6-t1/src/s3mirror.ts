// Provided: a local stand-in for S3 ListObjectsV2 / GetObject over incident/s3/<bucket>/<key>.
import * as fs from "fs";
import * as path from "path";

export class LocalS3 {
  constructor(private root: string) {}

  /** Every key under the prefix, recursively, like ListObjectsV2 without a delimiter. Sorted. */
  list(bucket: string, prefix: string): string[] {
    const base = path.join(this.root, bucket);
    const out: string[] = [];
    const walk = (dir: string) => {
      if (!fs.existsSync(dir)) return;
      for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
        const p = path.join(dir, e.name);
        if (e.isDirectory()) walk(p);
        else out.push(path.relative(base, p).split(path.sep).join("/"));
      }
    };
    walk(base);
    return out.filter((k) => k.startsWith(prefix)).sort();
  }

  getJson(bucket: string, key: string): any {
    return JSON.parse(fs.readFileSync(path.join(this.root, bucket, key), "utf8"));
  }
}
