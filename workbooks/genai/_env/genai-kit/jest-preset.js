"use strict";
// Shared jest config for genai exercises: ts-jest (transpile only, so a type error in one file
// does not hide every test), tests under tests/ (visible) and tests/__hidden__ (grader).
// Usage in an exercise's jest.config.js:
//   module.exports = require("genai-kit/jest-preset")({ env: "node" });   // or "jsdom"
module.exports = function preset(opts = {}) {
  const env = opts.env || "node";
  return {
    rootDir: process.cwd(),
    testEnvironment: env,
    roots: ["<rootDir>"],
    testMatch: ["<rootDir>/tests/**/*.test.ts", "<rootDir>/tests/**/*.test.tsx"],
    testPathIgnorePatterns: ["/node_modules/", "/.grading/"],
    modulePathIgnorePatterns: ["<rootDir>/.grading/"],
    transform: {
      "^.+\\.tsx?$": ["ts-jest", {
        diagnostics: false,
        tsconfig: {
          target: "ES2022", module: "commonjs", esModuleInterop: true, jsx: "react-jsx",
          strict: true, skipLibCheck: true, resolveJsonModule: true, isolatedModules: true,
        },
      }],
    },
    ...(env === "jsdom" ? { setupFilesAfterEnv: [require.resolve("@testing-library/jest-dom")] } : {}),
    testTimeout: opts.testTimeout || 15000,
    ...(opts.extra || {}),
  };
};
