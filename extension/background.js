import { runCheck, saveToShelf, askAgent, getEvidence } from "./check.js";
import { API_BASE, SHELF_SYNC } from "./config.js";
import { callOp, opsStatus } from "./ops.js";

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
  const entry = { id, product_id: item.product_id, title: meta.title || meta.url, url: meta.url, host: meta.host, level: meta.level || null, saved_at: item.added_at || new Date().toISOString(), next_check: item.next_check || null, synced: !!item.synced };
  await chrome.storage.local.set({ shelf: [entry, ...shelf.filter((i) => i.id !== id)].slice(0, 200) });
}

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  const jobs = {
    "safeshelf:check": async () => { await mustBeOn(); return runCheck(msg.page); },
    "safeshelf:cost-info": async () => ({ mockApi: /\/\/(localhost|127\.0\.0\.1)/.test(API_BASE) }), // TEMP cost guard
    "safeshelf:call": async () => { await mustBeOn(); return callOp(msg.op, msg.args || {}); }, // any API operation, only if it is live
    "safeshelf:status": async () => opsStatus(),
    "safeshelf:open-lab": async () => chrome.tabs.create({ url: chrome.runtime.getURL("lab.html") }),
    "safeshelf:evidence": async () => { await mustBeOn(); return getEvidence(msg.ids || []); },
    "safeshelf:chat": async () => { await mustBeOn(); return askAgent(msg); },
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
    "safeshelf:open-shelf": async () => chrome.tabs.create({ url: chrome.runtime.getURL("shelf.html") }),
  };
  if (!jobs[msg?.type]) return;
  jobs[msg.type]()
    .then((result) => reply({ ok: true, result }))
    .catch((err) => reply({ ok: false, error: err.message }));
  return true; // answer asynchronously
});
