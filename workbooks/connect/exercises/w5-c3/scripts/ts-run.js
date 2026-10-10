// Minimal TypeScript runner (transpile-only) so `make eval` needs nothing beyond the shared toolchain.
const fs = require("fs");
const ts = require("typescript");
require.extensions[".ts"] = function (module, filename) {
  const out = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
    fileName: filename,
  });
  module._compile(out.outputText, filename);
};
const [, , script, ...rest] = process.argv;
process.argv = [process.argv[0], script, ...rest];
require(require("path").resolve(script));
