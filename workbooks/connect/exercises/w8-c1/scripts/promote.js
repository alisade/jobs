// Run src/cli.ts without a build step: transpile .ts on require with the shared typescript.
const fs = require("fs");
const ts = require("typescript");
require.extensions[".ts"] = (m, file) => {
  const out = ts.transpileModule(fs.readFileSync(file, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
    fileName: file,
  }).outputText;
  m._compile(out, file);
};
if (process.argv[2]) process.env.ENV = process.argv[2];
require("../src/cli.ts");
