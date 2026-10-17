// My Shelf, kept in this browser (chrome.storage.local "shelf") and, while someone is signed in, also in their
// account: Firestore users/{uid}/shelf/{doc}, which the website's My Shelf page (web/site/shelf.html) reads and
// edits. firestore.rules lets each person read and write only their own shelf. Every change to the local shelf goes
// through `shelfChange`, one at a time, so a sync never overwrites a save that happened in between.
//
// Each local item remembers the account it was uploaded to (`cloud: uid`). On a sync, an item that was uploaded but
// is no longer in the account was removed on the website (or belongs to another account), so it goes here too;
// an item never uploaded (saved while signed out, or the upload failed) is uploaded now. Removals wait in
// "shelfDeleted" until Firestore has them, and an item waiting there is never brought back by a sync.
import { idToken, signedInUid } from "./session.js";

const PROJECT = "shelf2026-3656b";
const DOCS = `https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents`;
const FIELDS = ["key", "url", "title", "host", "image_url", "level", "product_id", "saved_at"];

let chain = Promise.resolve();
/** Run one change to the local shelf after the ones before it. */
export function shelfChange(job) {
  const run = chain.then(job);
  chain = run.catch(() => {});
  return run;
}

const getLocal = async () => (await chrome.storage.local.get("shelf")).shelf || [];
const setLocal = (shelf) => chrome.storage.local.set({ shelf });

// Firestore document ids cannot hold "/", and an item's id is "<product>|<listing url>", so the document is named
// after a hash of it.
async function docId(key) {
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(key));
  return [...new Uint8Array(hash)].slice(0, 20).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function firestore(path, init = {}) {
  const res = await fetch(`${DOCS}/${path}`, { ...init, signal: AbortSignal.timeout(15000),
    headers: { Authorization: `Bearer ${await idToken()}`, "Content-Type": "application/json" } });
  if (!res.ok && !(init.method === "DELETE" && res.status === 404)) throw new Error(`Your shelf couldn't sync (${res.status})`);
  return res.status === 204 || init.method === "DELETE" ? null : res.json();
}

const toFields = (item) => Object.fromEntries(FIELDS.map((f) => {
  const v = f === "key" ? item.id : item[f];
  return [f, typeof v === "string" && v ? { stringValue: v.slice(0, 2000) } : { nullValue: null }];
}));
const fromDoc = (doc) => {
  const f = Object.fromEntries(FIELDS.map((k) => [k, doc.fields?.[k]?.stringValue ?? null]));
  return { id: f.key, doc: String(doc.name || "").split("/").pop() || null, product_id: f.product_id, title: f.title, url: f.url, image_url: f.image_url, host: f.host, level: f.level, saved_at: f.saved_at };
};

const upload = async (uid, item) => firestore(`users/${uid}/shelf/${item.doc || await docId(item.id)}`, { method: "PATCH", body: JSON.stringify({ fields: toFields(item) }) });
const drop = async (uid, key, doc) => firestore(`users/${uid}/shelf/${doc || await docId(key)}`, { method: "DELETE" });

async function listRemote(uid) {
  const items = [];
  let page = "";
  do {
    const r = await firestore(`users/${uid}/shelf?pageSize=300${page ? `&pageToken=${encodeURIComponent(page)}` : ""}`);
    items.push(...(r.documents || []).map(fromDoc).filter((i) => i.id));
    page = r.nextPageToken || "";
  } while (page);
  return items;
}

/** Upload one saved item to the signed-in account; marks it uploaded. Never throws: the next sync retries. */
export async function pushItem(id) {
  const uid = await signedInUid();
  if (!uid) return false;
  try {
    return await shelfChange(async () => {
      const item = (await getLocal()).find((i) => i.id === id);
      if (!item) return false; // removed meanwhile
      await upload(uid, item);
      await setLocal((await getLocal()).map((i) => (i.id === id ? { ...i, cloud: uid } : i)));
      return true;
    });
  } catch (_) { return false; }
}

/** Take items off the shelf here and in the account. `keep(item)` says which stay; returns how many left. */
export async function removeFromShelf(keep) {
  const removed = await shelfChange(async () => {
    const local = await getLocal();
    const gone = local.filter((i) => !keep(i));
    if (!gone.length) return 0;
    // written down first, so a sync that runs before the delete reaches Firestore doesn't bring the item back
    const { shelfDeleted = [] } = await chrome.storage.local.get("shelfDeleted");
    const add = gone.filter((i) => i.cloud).map((i) => ({ uid: i.cloud, key: i.id, doc: i.doc || null }));
    await chrome.storage.local.set({ shelf: local.filter(keep), shelfDeleted: [...shelfDeleted, ...add].slice(-500) });
    return gone.length;
  });
  if (removed) await shelfChange(flushDeletes).catch(() => {});
  return removed;
}

// Sends the waiting removals for the signed-in account; throws if one can't be sent (the rest still wait).
async function flushDeletes() {
  const uid = await signedInUid();
  const { shelfDeleted = [] } = await chrome.storage.local.get("shelfDeleted");
  const waiting = [];
  let error = null;
  for (const d of shelfDeleted) {
    if (d.uid !== uid || error) { waiting.push(d); continue; }
    try { await drop(uid, d.key, d.doc); } catch (err) { error = err; waiting.push(d); }
  }
  await chrome.storage.local.set({ shelfDeleted: waiting });
  if (error) throw error;
  return waiting;
}

/** Bring the local shelf and the account's shelf together. Returns {signedIn, synced, error?}. */
export async function syncShelf() {
  const uid = await signedInUid();
  if (!uid) return { signedIn: false, synced: false };
  try {
    // one step, so a save or removal can't land between reading the account and writing the merged shelf
    const toUpload = await shelfChange(async () => {
      await flushDeletes();
      const remote = await listRemote(uid);
      const remoteIds = new Set(remote.map((i) => i.id));
      const local = await getLocal();
      const byId = new Map(local.map((i) => [i.id, i]));
      const fresh = local.filter((i) => !i.cloud && !remoteIds.has(i.id));
      const merged = [
        // the account's copy wins, but a photo or verdict only this browser has is kept
        ...remote.map((r) => { const l = byId.get(r.id) || {}; return { ...l, ...r, image_url: r.image_url || l.image_url || null, level: r.level || l.level || null, cloud: uid }; }),
        ...fresh,
      ].sort((a, b) => String(b.saved_at).localeCompare(String(a.saved_at))).slice(0, 200);
      await setLocal(merged);
      return fresh;
    });
    for (const item of toUpload) await pushItem(item.id);
    return { signedIn: true, synced: true };
  } catch (err) {
    return { signedIn: true, synced: false, error: err.message };
  }
}
