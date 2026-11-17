const path = require("path");
const envDir = process.env.AIARCH_ENV_DIR || path.join(__dirname, "..", "..", "_env");
module.exports = require(path.join(envDir, "jest-preset.js"))({ testTimeout: 90000 });
