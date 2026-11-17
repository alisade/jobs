// fastify.inject loads the ESM-only cookie package, which jest cannot require(); map it to a shim.
module.exports = require("bk-kit/jest-preset")({
  testTimeout: 30000,
  extra: { moduleNameMapper: { "^cookie$": "<rootDir>/jest/cookie-shim.js" } },
});
