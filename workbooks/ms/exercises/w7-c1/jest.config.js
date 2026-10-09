/** Jest config: ts-jest + jsdom, the same DOM APIs a model-driven form gives a PCF control. */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  roots: ["<rootDir>/tests"],
  testMatch: ["**/*.test.ts"],
};
