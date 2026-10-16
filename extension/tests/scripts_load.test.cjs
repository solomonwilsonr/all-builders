// content.js and lab.js must load without errors against a stand-in page (a syntax check cannot catch load-order mistakes).
const { read, fake, chromeStub, vm } = require("./helpers.cjs");
const assert = require("assert");

{ // content.js, loaded after panels.js exactly like the manifest does
  const ctx = {
    document: { createElement: () => fake(), createElementNS: () => fake(), createTreeWalker: () => ({ nextNode: () => null }), querySelector: () => null, querySelectorAll: () => [],
      body: Object.assign(fake(), { dataset: { safeshelfListingId: "SS-L-1" }, innerText: "x" }), documentElement: fake(), addEventListener() {}, removeEventListener() {} },
    location: { hostname: "localhost", href: "http://localhost:8090/product.html", pathname: "/product.html", search: "", hash: "", origin: "http://localhost:8090" },
    chrome: chromeStub(() => ({ result: { mockApi: true } })), NodeFilter: { SHOW_TEXT: 4 }, speechSynthesis: { cancel() {}, speak() {} }, SpeechSynthesisUtterance: function () {},
    setInterval: () => 1, clearInterval() {}, setTimeout: () => 1, clearTimeout() {}, innerWidth: 1200, innerHeight: 800, console, URL, Promise, JSON, Set, Map, Array, Object, Number, String, RegExp, Math, Date, Error,
  };
  ctx.window = ctx.globalThis = ctx; vm.createContext(ctx);
  vm.runInContext(read("panels.js"), ctx);
  assert.doesNotThrow(() => vm.runInContext(read("aftercare.js"), ctx), "aftercare.js failed to load");
  assert.ok(ctx.SafeShelfAftercare?.guardBuy, "aftercare.js should expose SafeShelfAftercare");
  assert.doesNotThrow(() => vm.runInContext(read("content.js"), ctx), "content.js failed to load");
}
{ // lab.js
  const sent = [];
  const ctx = { document: { getElementById: () => fake(), querySelector: () => fake(), querySelectorAll: () => [], createElement: () => fake() },
    chrome: chromeStub((m) => { sent.push(m.type); return { ok: true, result: m.type === "safeshelf:status" ? [{ op: "trustCheck", method: "POST", path: "/x", live: true }] : { live: false } }; }),
    confirm: () => true, console, Object, Promise };
  ctx.globalThis = ctx; vm.createContext(ctx);
  vm.runInContext(read("panels.js"), ctx);
  assert.doesNotThrow(() => vm.runInContext(read("lab.js"), ctx), "lab.js failed to load");
  assert.ok(sent.includes("safeshelf:status"), "the Lab should ask for the API status on load");
}
console.log("ok  scripts_load");
