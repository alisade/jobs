"use strict";
// Shared jest config for backend exercises: ts-jest (transpile only, so a type error in one
// file does not hide every test), tests under tests/ (visible) and tests/__hidden__ (grader).
// Usage in an exercise's jest.config.js:
//   module.exports = require("bk-kit/jest-preset")();
module.exports = function preset(opts = {}) {
  return {
    rootDir: process.cwd(),
    testEnvironment: "node",
    roots: ["<rootDir>"],
    testMatch: ["<rootDir>/tests/**/*.test.ts"],
    testPathIgnorePatterns: ["/node_modules/", "/.grading/"],
    modulePathIgnorePatterns: ["<rootDir>/.grading/"],
    transform: {
      "^.+\\.tsx?$": ["ts-jest", {
        diagnostics: false,
        tsconfig: {
          target: "ES2022", module: "commonjs", esModuleInterop: true,
          strict: true, skipLibCheck: true, resolveJsonModule: true, isolatedModules: true,
        },
      }],
    },
    testTimeout: opts.testTimeout || 30000,
    ...(opts.extra || {}),
  };
};
