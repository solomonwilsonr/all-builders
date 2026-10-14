// The card's tabs: which API calls each match type makes, and the banners that keep a look-alike honest.
const { read, el } = require("./helpers.cjs");
const assert = require("assert");
const src = read("content.js");
const code = src.slice(src.indexOf("    const panelTabs = (r, overviewNodes) => {"), src.indexOf("    const render = (r) => {"));

function run(r) {
  const log = [];
  const ctx = { el, place() {}, getPage: () => ({ url: "u" }), NOT_LIVE: "NOT LIVE",
    loadPanel: (into, op, args) => { log.push(`${op}(${args.product_id || "listing"})`); into.replaceChildren(el("div", { textContent: `[loaded ${op}]` })); },
    costlyButton: (label) => el("button", { textContent: label }), chrome: { runtime: { sendMessage: (m, cb) => cb({ ok: true, result: [{ op: "report", live: true }] }) } } };
  const panelTabs = new Function(...Object.keys(ctx), `${code}; return panelTabs;`)(...Object.values(ctx));
  const root = panelTabs(r, [el("p", { textContent: "overview content" })]);
  const area = root.kids[1], seen = {};
  for (const b of root.kids[0].kids) { b.click(); seen[b.textContent] = area.text(); }
  return { log, seen };
}

let t = run({ product_id: "SS-P-EXACT" });
assert.deepStrictEqual(t.log, ["certifications(SS-P-EXACT)", "relationships(SS-P-EXACT)", "history(SS-P-EXACT)", "alternatives(SS-P-EXACT)", "product(SS-P-EXACT)"]);
assert.match(t.seen["Report"], /Send report/);

t = run({ product_id: null, similar_product_id: "SS-P-IN-9F" }); // a look-alike match
assert.strictEqual(t.log.length, 5, "a look-alike still gets its lookups");
for (const tab of ["Marks", "Copies", "History", "Safer options", "Details"]) assert.match(t.seen[tab], /similar product \(SS-P-IN-9F\), not this exact listing/, `${tab} must carry the similar-product banner`);
assert.match(t.seen["Report"], /needs an exact product match/, "a report about a different product must not be possible");

t = run({ product_id: null, similar_product_id: null });
assert.deepStrictEqual(t.log, [], "no match: no API calls");
assert.match(t.seen["Marks"], /no product in its catalog/);
console.log("ok  tabs");
