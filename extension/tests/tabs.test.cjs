// The card shows only the Overview for now: no tab bar, and none of the other tabs' API calls (marks, safer options, details, report).
const { read, el } = require("./helpers.cjs");
const assert = require("assert");
const src = read("content.js");
const code = src.slice(src.indexOf("    const panelTabs = (r, overviewNodes, historyBtn, historyPanel) => {"), src.indexOf("    const render = (r, fresh = false) => {"));

function run(r) {
  const log = [];
  const ctx = { el, place() {}, getPage: () => ({ url: "u" }), NOT_LIVE: "NOT LIVE",
    loadPanel: (into, op, args) => { log.push(`${op}(${args.product_id || "listing"})`); into.replaceChildren(el("div", { textContent: `[loaded ${op}]` })); },
    costlyButton: (label) => el("button", { textContent: label }), chrome: { runtime: { sendMessage: (m, cb) => cb({ ok: true, result: [{ op: "report", live: true }] }) } } };
  const panelTabs = new Function(...Object.keys(ctx), `${code}; return panelTabs;`)(...Object.values(ctx));
  const root = panelTabs(r, [el("p", { textContent: "overview content" })]);
  return { log, root };
}

for (const r of [{ product_id: "SS-P-EXACT" }, { product_id: null, similar_product_id: "SS-P-IN-9F" }, { product_id: null, similar_product_id: null }]) {
  const { log, root } = run(r);
  assert.strictEqual(root.kids.length, 1, "no tab bar: just the Overview panel");
  assert.match(root.kids[0].text(), /overview content/);
  assert.deepStrictEqual(log, [], "no tab makes an API call");
}
console.log("ok  tabs");
