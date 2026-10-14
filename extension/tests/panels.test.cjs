// panels.js: every API answer shape (the contract's examples, plus the real bench result) becomes sensible rows.
const { read, mock, vm } = require("./helpers.cjs");
const assert = require("assert");
const ctx = {}; ctx.globalThis = ctx; vm.createContext(ctx); vm.runInContext(read("panels.js"), ctx);
const P = ctx.SafeShelfPanels;

const cert = P.certifications(mock("certifications"));
assert.strictEqual(cert.rows[0].icon, "⛔"); assert.match(cert.rows[0].text, /registry says 3 stars/);
assert.strictEqual(cert.rows[1].icon, "❔");
assert.strictEqual(P.relationships(mock("relationships")).rows.length, 3);
assert.match(P.duplicates(mock("duplicates")).rows[1].sub, /Differ: different brand name/);
assert.strictEqual(P.history(mock("history")).rows[1].icon, "⚠️");
assert.match(P.alternatives(mock("alternatives")).rows[0].sub, /₹1,450/);
assert.ok(P.product(mock("product")).rows.some((r) => /Brand: ExampleBrand/.test(r.text)));
assert.match(P.report(mock("report_created")).rows[0].text, /SS-R-0001/);
assert.match(P.catalogScan(mock("catalog_scan")).title, /14 of your 2,300/);
assert.match(P.trace(mock("trace")).rows[0].sub, /₹0\.04/);
for (const f of [P.certifications, P.relationships, P.history, P.alternatives]) assert.ok(f({}).empty, "an empty answer must say so, not show nothing");

// The real backtest result's shape (Person A's /v1/bench/results)
const bench = P.bench({ generated_at: "2026-10-13T12:07:32+00:00",
  tasks: { early_warning: { keyword_rules: { recalls_flagged: "11/25", median_lead_weeks: 169.9, false_alarm_rate: 0.28, false_alarms: "11/40" }, safeshelf: { recalls_flagged: "6/25", median_lead_weeks: 92.6, false_alarm_rate: 0.05, false_alarms: "2/40" } } },
  safeshelf_on_test_half: { recalls_flagged: "2/9", median_lead_weeks: 71.7, false_alarm_rate: 0, false_alarms: "0/14" }, caveats: ["Read this."],
  per_recall: [{ title: "T", recall_date: "2023-01-01", listings: 1, reviews_before_recall: 0, split: "train", keyword_rules_lead_days: null, gemini_alone_lead_days: null, safeshelf_lead_days: 10 }], controls: [{}] });
assert.ok(bench.rows.some((r) => /Held-out test half/.test(r.heading)), "the unbiased test-half figure must be shown");
assert.ok(bench.rows.some((r) => /false alarms 2\/40 \(5%\)/.test(r.sub || "")));
assert.ok(bench.rows.some((r) => r.text === "Read this."), "caveats must be shown");
console.log("ok  panels");
