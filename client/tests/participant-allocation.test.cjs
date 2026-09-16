const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const config = fs.readFileSync(path.join(root, "src/experiment/experimentConfig.js"), "utf8");
const api = fs.readFileSync(path.join(root, "src/experiment/experimentApi.js"), "utf8");

for (let i = 1; i <= 24; i++) assert.match(config, new RegExp(`P${String(i).padStart(2, "0")}`));
for (const condition of ["TE", "CS", "SE", "BL"]) assert.match(config, new RegExp(`['\"]${condition}['\"]`));
assert.match(api, /\/sessions/);
assert.match(api, /responses/);
assert.match(api, /events/);
assert.match(api, /interview/);
assert.doesNotMatch(api, /(?:startSession|post)[\s\S]{0,220}\bmode\b/);
const app = fs.readFileSync(path.join(root, "src/App.vue"), "utf8");
const picker = fs.readFileSync(path.join(root, "src/components/experiment/ParticipantPicker.vue"), "utf8");
assert.doesNotMatch(app, /experimentMode|:mode=/);
assert.doesNotMatch(picker, /props\.mode|mode:/);
console.log("participant allocation contract checks passed");
