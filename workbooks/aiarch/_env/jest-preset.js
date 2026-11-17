"use strict";
// Shared jest config for aiarch TypeScript exercises: ts-jest (transpile only, so a type error in
// one file does not hide every test), tests under tests/ (visible) and tests/__hidden__ (grader).
// Usage in an exercise's jest.config.js:
//   module.exports = require("../../_env/jest-preset.js")({ testTimeout: 60000 });
module.exports = function preset(opts = {}) {
  return {
    rootDir: process.cwd(),
    testEnvironment: "node",
    roots: ["<rootDir>"],
    testMatch: ["<rootDir>/tests/**/*.test.ts"],
    testPathIgnorePatterns: ["/node_modules/", "/.grading/", "/cdk.out/"],
    modulePathIgnorePatterns: ["<rootDir>/.grading/", "<rootDir>/cdk.out/"],
    transform: {
      "^.+\\.tsx?$": [require.resolve("ts-jest", { paths: [__dirname] }), {
        diagnostics: false,
        tsconfig: {
          target: "ES2022", module: "commonjs", esModuleInterop: true,
          strict: true, skipLibCheck: true, resolveJsonModule: true, isolatedModules: true,
        },
      }],
    },
    testTimeout: opts.testTimeout || 60000,
    ...(opts.extra || {}),
  };
};
