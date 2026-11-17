// ts-jest in transpile-only mode: a type error in one file does not hide every test.
// Visible tests live in tests/, the grader adds tests/__hidden__/.
module.exports = {
  rootDir: __dirname,
  testEnvironment: "node",
  testMatch: ["<rootDir>/tests/**/*.test.ts"],
  testPathIgnorePatterns: ["/node_modules/", "/.grading/"],
  modulePathIgnorePatterns: ["<rootDir>/.grading/"],
  transform: {
    "^.+\\.ts$": ["ts-jest", { diagnostics: false, tsconfig: "<rootDir>/tsconfig.json" }],
  },
  testTimeout: 10000,
};
