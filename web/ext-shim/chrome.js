// The SafeShelf extension, running inside the judges' page ("Try a sample"): a stand-in for the chrome.* functions
// the real extension files use (web/ext/, copied from extension/ by `make web-ext`). Content scripts and the
// background code run in this one frame, so messages are handed straight from one to the other.
// Sign-in comes from the judges' page around this frame (session.js here), so the widget never asks for it.
(() => {
  const KEY = "safeshelf-web-extension";
  let store = {};
  try { store = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (_) { /* private mode: settings last for this visit */ }
  store = { enabled: true, costGuard: true, ...store };
  const persist = () => { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (_) {} };
  const settle = (value, cb) => { const p = Promise.resolve(value); if (cb) { p.then(cb); return undefined; } return p; };
  const copy = (v) => (v === undefined ? v : JSON.parse(JSON.stringify(v)));

  const changeListeners = [];
  const background = [], content = []; // onMessage listeners of each side
  const connectListeners = [];
  const side = () => (globalThis.__safeshelfPhase === "background" ? background : content);

  // Every check is about the listing this tab stands for: its exact link, title, price, seller and page text.
  const listing = () => globalThis.__safeshelfListing || null;
  const rewrite = (msg) => {
    const l = listing();
    if (!l || !msg || typeof msg !== "object") return msg;
    const m = { ...msg };
    if (m.page) m.page = { ...m.page, ...l };
    if (m.meta) m.meta = { ...m.meta, url: l.url, title: l.title || m.meta.title };
    if (m.url && m.type === "safeshelf:unsave") m.url = l.url;
    if (m.body?.listing) m.body = { ...m.body, listing: { ...m.body.listing, ...l } };
    return m;
  };
  // Paid calls count against the judges' page limit (10 live runs a day on this browser).
  const PAID = new Set(["safeshelf:check", "safeshelf:agent", "safeshelf:chat"]);
  const host = () => { try { return window.parent?.SafeShelfDemo || null; } catch (_) { return null; } };
  const allowPaid = () => {
    const q = host()?.quota;
    if (!q) return true;
    if (!q.left()) return false;
    q.take();
    return true;
  };
  const deliver = (listeners, msg, sender) => new Promise((resolve) => {
    let answered = false, waiting = false;
    const reply = (r) => { if (!answered) { answered = true; resolve(r); } };
    for (const l of listeners) { try { if (l(msg, sender, reply) === true) waiting = true; } catch (err) { reply({ ok: false, error: err.message }); } }
    if (!waiting && !answered) resolve(undefined);
  });
  const sender = { id: "safeshelf-web", url: location.href, origin: location.origin, tab: { id: 1, url: location.href } };

  const port = (name) => {
    const ls = { message: [], disconnect: [] };
    return {
      name, sender, _ls: ls, _peer: null,
      onMessage: { addListener: (f) => ls.message.push(f), removeListener() {} },
      onDisconnect: { addListener: (f) => ls.disconnect.push(f), removeListener() {} },
      postMessage(m) { const peer = this._peer; const msg = this._fromContent ? rewrite(m) : m; setTimeout(() => peer?._ls.message.forEach((f) => f(msg, peer)), 0); },
      disconnect() { const peer = this._peer; setTimeout(() => peer?._ls.disconnect.forEach((f) => f(peer)), 0); },
    };
  };

  globalThis.chrome = {
    runtime: {
      id: "safeshelf-web",
      lastError: undefined,
      getManifest: () => globalThis.__safeshelfManifest || { name: "SafeShelf", version: "" },
      getURL: (p) => new URL(`ext/${String(p).replace(/^\//, "")}`, location.href).href,
      getPlatformInfo: () => Promise.resolve({ os: "web" }),
      onMessage: { addListener: (f) => side().push(f), removeListener: (f) => { for (const a of [background, content]) { const i = a.indexOf(f); if (i >= 0) a.splice(i, 1); } } },
      onConnect: { addListener: (f) => connectListeners.push(f), removeListener() {} },
      onInstalled: { addListener() {} }, onStartup: { addListener() {} }, onMessageExternal: { addListener() {} },
      sendMessage(msg, cb) {
        const m = rewrite(msg);
        const p = PAID.has(m?.type) && !allowPaid()
          ? Promise.resolve({ ok: false, error: "Live checks are used up on this browser today. The saved sample runs still work on the judges' page." })
          : deliver(background, m, sender);
        if (cb) { p.then(cb); return undefined; }
        return p;
      },
      connect({ name } = {}) {
        if (!allowPaid()) {
          const dead = port(name);
          setTimeout(() => dead._ls.message.forEach((f) => f({ type: "error", error: "Live checks are used up on this browser today." }, dead)), 0);
          return dead;
        }
        const a = port(name), b = port(name);
        a._peer = b; b._peer = a; a._fromContent = true;
        connectListeners.forEach((f) => f(b));
        return a;
      },
    },
    storage: {
      local: {
        get(keys, cb) {
          const out = {};
          if (keys && typeof keys === "object" && !Array.isArray(keys)) Object.assign(out, keys);
          const list = keys == null ? Object.keys(store) : typeof keys === "string" ? [keys] : Array.isArray(keys) ? keys : Object.keys(keys);
          for (const k of list) if (k in store) out[k] = copy(store[k]);
          return settle(out, cb);
        },
        set(obj, cb) {
          const changes = {};
          for (const [k, v] of Object.entries(obj || {})) { changes[k] = { oldValue: store[k], newValue: copy(v) }; store[k] = copy(v); }
          persist();
          setTimeout(() => changeListeners.forEach((l) => l(changes, "local")), 0);
          return settle(undefined, cb);
        },
        remove(keys, cb) {
          const changes = {};
          for (const k of [].concat(keys)) { changes[k] = { oldValue: store[k] }; delete store[k]; }
          persist();
          setTimeout(() => changeListeners.forEach((l) => l(changes, "local")), 0);
          return settle(undefined, cb);
        },
      },
      onChanged: { addListener: (f) => changeListeners.push(f), removeListener: (f) => { const i = changeListeners.indexOf(f); if (i >= 0) changeListeners.splice(i, 1); } },
    },
    action: { setBadgeText: () => Promise.resolve(), setBadgeBackgroundColor: () => Promise.resolve() },
    tabs: {
      create: ({ url } = {}) => { host()?.notice?.(/shelf\.html/.test(url || "") ? "My Shelf lives in the installed extension. Here, saved products stay in this browser." : "That page opens in the installed extension."); return Promise.resolve({ id: 2 }); },
      remove: () => Promise.resolve(),
      query: (_q, cb) => settle([{ id: 1, url: listing()?.url || location.href }], cb),
      sendMessage: (_id, msg, cb) => { const p = deliver(content, msg, { id: "safeshelf-web" }); if (cb) { p.then(cb); return undefined; } return p; },
    },
  };
})();
