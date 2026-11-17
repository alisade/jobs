// Run a .ts entry point without a build step (transpile on require with the shared typescript).
const fs = require("fs");
const path = require("path");
const ts = require("typescript");
require.extensions[".ts"] = (m, file) => {
  const out = ts.transpileModule(fs.readFileSync(file, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
    fileName: file,
  }).outputText;
  m._compile(out, file);
};
const target = process.argv[2];
process.argv.splice(1, 2);
require(path.resolve(target));
