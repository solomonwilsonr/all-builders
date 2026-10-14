// Shared by the extension tests: a stand-in page and browser, so the scripts can run in plain Node (no Chrome, no network).
const fs = require("fs"), path = require("path"), vm = require("vm");
const EXT = path.resolve(__dirname, "..");
const read = (f) => fs.readFileSync(path.join(EXT, f), "utf8");
const mock = (n) => JSON.parse(fs.readFileSync(path.join(EXT, "..", "contracts", "mock", n + ".json"), "utf8"));

// An object that accepts any property access or call: stands in for the DOM.
const fake = () => new Proxy(function () {}, {
  get: (t, k) => (k === Symbol.toPrimitive ? () => "" : k === "length" ? 0 : k === "then" ? undefined : k === "isConnected" ? false :
    ["innerText", "textContent", "src", "content", "value"].includes(k) ? "" : k === "dataset" || k === "style" ? {} : k === "children" || k === "attributes" ? [] : fake()),
  set: () => true, apply: () => fake(), construct: () => fake(),
});

// A tiny DOM with real children and click handlers, for testing logic that builds and swaps elements.
class E {
  constructor(tag) { this.tag = tag; this.kids = []; }
  append(...k) { this.kids.push(...k); }
  replaceChildren(...k) { this.kids = k; }
  setAttribute() {}
  focus() {}
  click() { this.onclick && this.onclick(); }
  text() { return (this.textContent || "") + this.kids.map((k) => (typeof k === "string" ? k : k.text())).join(" | "); }
}
const el = (tag, props = {}, ...kids) => { const n = new E(tag); Object.assign(n, props); n.append(...kids); return n; };

const chromeStub = (onMessage = () => {}) => ({
  runtime: { lastError: null, sendMessage: (m, cb) => { const r = onMessage(m); cb && cb(r); return Promise.resolve(r); }, onMessage: { addListener() {}, removeListener() {} }, getManifest: () => ({ version: "test" }) },
  storage: { local: { get: (k, cb) => { const r = {}; cb ? cb(r) : 0; return Promise.resolve(r); }, set: () => Promise.resolve() }, onChanged: { addListener() {}, removeListener() {} } },
});
module.exports = { EXT, read, mock, fake, el, E, chromeStub, vm };
