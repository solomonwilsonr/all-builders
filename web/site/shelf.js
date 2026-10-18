// My Shelf on the website: the products the person saved with the extension, kept in Firestore under their account
// (users/{uid}/shelf, written by extension/shelf-sync.js; firestore.rules lets each person see only their own).
// The list updates live; Remove deletes the item here, and the extension drops it on its next sync.
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { collection, deleteDoc, doc, onSnapshot } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js";
import { firebaseArea } from "../firebase-app.js?v=20261017v";

const { auth, db } = firebaseArea("site");
const LABEL = { green: "Looks fine so far", amber: "Under review", red: "Needs attention", unknown: "Not checked yet" };
const $ = (id) => document.getElementById(id);
const make = (tag, props = {}, ...kids) => { const e = Object.assign(document.createElement(tag), props); e.append(...kids); return e; };
const safeURL = (v) => { try { const u = new URL(v); return ["http:", "https:"].includes(u.protocol) ? u.href : null; } catch (_) { return null; } };
const levelOf = (i) => (["green", "amber", "red"].includes(i.level) ? i.level : "unknown");

let items = [];
let stop = null;

function state(text, button) {
  $("shelf").hidden = true;
  const box = make("div", { className: "box" }, make("p", { textContent: text }));
  if (button) box.append(button);
  $("state").replaceChildren(box);
  $("state").hidden = false;
}

function render() {
  const week = Date.now() - 7 * 864e5;
  $("n-total").textContent = items.length;
  $("n-attention").textContent = items.filter((i) => ["amber", "red"].includes(i.level)).length;
  $("n-unchecked").textContent = items.filter((i) => levelOf(i) === "unknown").length;
  $("n-recent").textContent = items.filter((i) => Date.parse(i.saved_at) >= week).length;
  $("n-count").textContent = items.length;

  const q = $("q").value.trim().toLowerCase();
  const f = $("f").value;
  const shown = items.filter((i) => `${i.title || ""} ${i.host || ""}`.toLowerCase().includes(q) && (f === "all" || levelOf(i) === f));
  $("none").hidden = !items.length || shown.length > 0;
  $("list").replaceChildren(...shown.map((i) => {
    const url = safeURL(i.url);
    const pic = make(url ? "a" : "div", { className: "pic", ...(url ? { href: url, target: "_blank", rel: "noopener" } : {}) });
    const img = safeURL(i.image_url);
    if (img) {
      const el = make("img", { src: img, alt: "", loading: "lazy", referrerPolicy: "no-referrer" });
      el.addEventListener("error", () => el.replaceWith("No image saved"), { once: true });
      pic.append(el);
    } else pic.append("No image saved");
    const name = make(url ? "a" : "span", { className: "name", textContent: i.title || "Saved product", ...(url ? { href: url, target: "_blank", rel: "noopener" } : {}) });
    const remove = make("button", { type: "button", textContent: "Remove" });
    remove.setAttribute("aria-label", `Remove ${i.title || "product"} from My Shelf`);
    remove.onclick = async () => {
      remove.disabled = true;
      try { await deleteDoc(doc(db, "users", auth.currentUser.uid, "shelf", i.docId)); }
      catch (_) { remove.disabled = false; remove.textContent = "Retry removal"; }
    };
    const d = new Date(i.saved_at);
    const saved = Number.isNaN(d.getTime()) ? "Saved" : `Saved ${d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}`;
    return make("li", { className: "item" }, pic, make("div", { className: "body" },
      make("span", { className: "host", textContent: i.host || "Saved listing" }), name,
      make("span", { className: `pill ${levelOf(i)}`, textContent: LABEL[levelOf(i)] }),
      make("div", { className: "foot-row" }, make("span", { textContent: saved }), remove)));
  }));
}

$("q").addEventListener("input", render);
$("f").addEventListener("change", render);

onAuthStateChanged(auth, (user) => {
  stop?.();
  stop = null;
  items = [];
  if (!user) {
    state("Products you save in the SafeShelf extension appear here.", make("a", { className: "btn btn-line", href: "get.html", textContent: "Get the extension" }));
    return;
  }
  stop = onSnapshot(collection(db, "users", user.uid, "shelf"), (snap) => {
    items = snap.docs.map((d) => ({ ...d.data(), docId: d.id })).sort((a, b) => String(b.saved_at).localeCompare(String(a.saved_at)));
    if (!items.length) {
      state(user.isAnonymous
        ? "Nothing saved yet. Products you save in the SafeShelf extension appear here."
        : "Nothing saved yet. In the SafeShelf extension, sign in with this account, then save a product from a shop page. It appears here right away.",
      make("a", { className: "btn btn-line", href: "get.html", textContent: "Get the extension" }));
      return;
    }
    $("state").hidden = true;
    $("shelf").hidden = false;
    render();
  }, () => state("Your shelf couldn't load. Check your connection and reload the page."));
});
