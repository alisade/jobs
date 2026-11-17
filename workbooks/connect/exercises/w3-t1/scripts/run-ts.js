// Minimal TypeScript runner for the make targets: transpiles .ts on require (no type check).
// Usage: node scripts/run-ts.js <file.ts> [args...]
const fs = require("fs");
const path = require("path");
const ts = require("typescript");
require.extensions[".ts"] = (module, filename) => {
  const out = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
    fileName: filename,
  });
  module._compile(out.outputText, filename);
};
const target = path.resolve(process.argv[2]);
process.env.RUN_TS_MAIN = target;
process.argv.splice(1, 2, target);
require(target);
