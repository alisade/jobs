"use strict";
// connect-kit: local stand-ins used by the connect workbook exercises. See README.md.
const flow = require("./flow");
const servicenow = require("./servicenow");

module.exports = { ...flow, ...servicenow };
