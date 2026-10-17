import { identity, requireAdmin, adminStatus } from "./rbac.js";
import { runCheck, reviewSummary, techCheck, priceCheck, saveToShelf, askAgent, getEvidence, agentSession, agentStream } from "./check.js";
import { API_BASE, SHELF_SYNC } from "./config.js";
import { callOp, opsStatus } from "./ops.js";
import { acceptSession, account, openSignIn, signOut, SIGNIN_ORIGINS } from "./session.js";

// The toolbar icon opens popup.html (My Shelf, on/off). The badge shows OFF while SafeShelf is turned off.
const isEnabled = async () => (await chrome.storage.local.get("enabled")).enabled !== false;
const syncBadge = async () => {
  await chrome.action.setBadgeText({ text: (await isEnabled()) ? "" : "OFF" });
  await chrome.action.setBadgeBackgroundColor({ color: "#b3261e" });
};
chrome.runtime.onInstalled.addListener(syncBadge);
chrome.runtime.onStartup.addListener(syncBadge);
chrome.storage.onChanged.addListener((changes) => { if (changes.enabled) syncBadge(); });

const mustBeOn = async () => { if (!(await isEnabled())) throw new Error("SafeShelf is turned off"); };

// Local copy of the shelf so it can be viewed before the live API and login exist (this browser only).
async function rememberLocally(item, meta) {
  const { shelf = [] } = await chrome.storage.local.get("shelf");
  const id = `${item.product_id || "unmatched"}|${meta.url}`;
  const entry = { id, product_id: item.product_id, title: meta.title || meta.url, url: meta.url, image_url: /^https?:\/\//i.test(meta.image_url || "") ? meta.image_url : null, host: meta.host, level: meta.level || null, saved_at: item.added_at || new Date().toISOString(), next_check: item.next_check || null, synced: !!item.synced };
  await chrome.storage.local.set({ shelf: [entry, ...shelf.filter((i) => i.id !== id)].slice(0, 200) });
}

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  const jobs = {
    "safeshelf:check": async () => { await mustBeOn(); return runCheck(msg.page, Boolean(msg.fresh)); },
    "safeshelf:reviews": async () => { await mustBeOn(); return reviewSummary(msg.listing); }, // "Is it any good?" widget
    "safeshelf:tech": async () => { await mustBeOn(); return techCheck(msg.listing); }, // "Is it possible?": the technology first
    "safeshelf:price": async () => { await mustBeOn(); return priceCheck(msg.listing, msg.claims || null); }, // then the price, if the technology can exist
    "safeshelf:cost-info": async () => ({ mockApi: /\/\/(localhost|127\.0\.0\.1)/.test(API_BASE) }), // TEMP cost guard
    "safeshelf:call": async () => { await mustBeOn(); if (["catalogScan", "bench"].includes(msg.op) || _sender.url === chrome.runtime.getURL("lab.html")) await requireAdmin(); return callOp(msg.op, msg.args || {}); }, // any API operation, only if it is live
    "safeshelf:status": async () => opsStatus(),
    "safeshelf:identity": async () => identity(),
    "safeshelf:set-cost-guard": async () => {
      await requireAdmin();
      if (typeof msg.enabled !== "boolean") throw new Error("Invalid paid-request setting");
      await chrome.storage.local.set({ costGuard: msg.enabled });
      return { costGuard: msg.enabled };
    },
    "safeshelf:admin-status": async () => adminStatus(),
    "safeshelf:lab-status": async () => { await requireAdmin(); return opsStatus(); },
    "safeshelf:open-lab": async () => { await requireAdmin(); return chrome.tabs.create({ url: chrome.runtime.getURL("lab.html") }); },
    "safeshelf:evidence": async () => { await mustBeOn(); return getEvidence(msg.ids || []); },
    "safeshelf:chat": async () => { await mustBeOn(); return askAgent(msg); },
    "safeshelf:agent": async () => { await mustBeOn(); return agentSession(msg.body || {}, Math.min(Number(msg.timeout) || 150000, 300000)); }, // Investigate and the other agents
    "safeshelf:save": async () => {
      await mustBeOn();
      // My Shelf lives in this browser. The API is only called when SHELF_SYNC is on (config.js).
      let item = { product_id: msg.product_id || null, added_at: new Date().toISOString(), next_check: null, synced: false };
      if (SHELF_SYNC) {
        try {
          const r = await saveToShelf({ product_id: msg.product_id || null, listing_url: msg.meta?.url, title: msg.meta?.title });
          // An example answer from an API that does not store shelf items yet is not a save, and its dates are not real.
          item = r.source === "mock" ? { ...item, api_mock: true } : { ...item, ...r, synced: true };
        } catch (err) {
          item.api_error = err.message; // e.g. the API requires a product id and this listing has none
        }
      }
      await rememberLocally(item, msg.meta || {});
      return item;
    },
    "safeshelf:unsave": async () => { // the bookmark on a product page, clicked again: My Shelf is in this browser, so removing it here is enough
      const { shelf = [] } = await chrome.storage.local.get("shelf");
      const left = shelf.filter((i) => i.url !== msg.url);
      await chrome.storage.local.set({ shelf: left });
      return shelf.length - left.length;
    },
    "safeshelf:shelf-image": async () => { // adds a photo to a saved product that has none; never replaces one
      if (!/^https?:\/\//i.test(msg.image_url || "")) return false;
      const { shelf = [] } = await chrome.storage.local.get("shelf");
      if (!shelf.some((i) => i.url === msg.url && !i.image_url)) return false;
      await chrome.storage.local.set({ shelf: shelf.map((i) => (i.url === msg.url && !i.image_url ? { ...i, image_url: msg.image_url } : i)) });
      return true;
    },
    "safeshelf:open-shelf": async () => chrome.tabs.create({ url: chrome.runtime.getURL("shelf.html") }),
    "safeshelf:account": async () => account(), // null: nobody is signed in
    "safeshelf:signin": async () => openSignIn(),
    "safeshelf:signout": async () => signOut(),
  };
  if (!jobs[msg?.type]) return;
  jobs[msg.type]()
    .then((result) => reply({ ok: true, result }))
    .catch((err) => reply({ ok: false, error: err.message, signin: err.name === "SignInNeeded" }));
  return true; // answer asynchronously
});

// The sign-in page (SIGNIN_URL) hands over the session after Google sign-in. Only the pages listed in the manifest's
// externally_connectable can send this, and only these origins are believed.
chrome.runtime.onMessageExternal.addListener((msg, sender, reply) => {
  if (msg?.type !== "safeshelf:session" || !SIGNIN_ORIGINS.includes(sender.origin)) return;
  acceptSession(msg)
    .then((who) => {
      reply({ ok: true, role: who.role });
      if (sender.tab?.id) setTimeout(() => chrome.tabs.remove(sender.tab.id).catch(() => {}), 2500); // the page says it closes by itself
    })
    .catch((err) => reply({ ok: false, error: err.message }));
  return true;
});

// Live agent sessions: a page opens a "safeshelf-agent" port, sends {body, timeout}, and gets every step as it
// happens ({type: "event"}), then {type: "done", result} or {type: "error", error}.
chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== "safeshelf-agent") return;
  let open = true;
  port.onDisconnect.addListener(() => { open = false; });
  const send = (m) => { if (open) port.postMessage(m); };
  port.onMessage.addListener(async (msg) => {
    // Chrome stops an extension worker after 30 s without an extension API call, which closed the port in the middle
    // of a first look's quiet minute on the recall sites (16 Oct, live: cut at 45 s). A cheap call every 20 s and a
    // ping for each piece of the stream (agentStream) keep it awake until the answer is in.
    const awake = setInterval(() => chrome.runtime.getPlatformInfo?.(), 20000);
    try {
      await mustBeOn();
      const result = await agentStream(msg.body || {}, (event) => send({ type: "event", event }), Math.min(Number(msg.timeout) || 150000, 300000));
      send({ type: "done", result });
    } catch (err) {
      send({ type: "error", error: err.message, signin: err.name === "SignInNeeded" });
    } finally {
      clearInterval(awake);
    }
  });
});
