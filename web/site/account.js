// Sign-in for the website: its own login, separate from the judges' demo (../firebase-app.js). The site stays
// readable signed out; the nav gets a "Sign in" button that opens the shared sign-in card (Google, email and
// password, or a guest). Signed in, the nav shows the person's photo (or "Guest") with a menu: who, checks left,
// My Shelf, Chat with Eddy, Try it live, Sign out. AI features (the chat) use window.safeshelfAccount.take() for each check:
// a guest gets 1 ever on this browser, an account 5 a day (../quota.js, counted in Firestore). Other scripts listen
// for "safeshelf:account"; window.safeshelfSignIn() opens the card.
import { onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { firebaseArea } from "../firebase-app.js?v=20261017v";
import { makeQuota } from "../quota.js?v=20261018u";
import { rememberAccount, signInCard } from "../signin-card.js?v=20261017v";

const { auth, db } = firebaseArea("site");
const quota = makeQuota(db, "site");

const end = document.querySelector(".nav-end");
const make = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k.includes("-") || k === "role") e.setAttribute(k, v);
    else e[k] = v;
  }
  e.append(...kids);
  return e;
};

// The sign-in card over the page; rebuilt each time so "Welcome back" shows the latest account.
let modal = null;
let opener = null;
function closeModal() {
  if (!modal) return;
  modal.remove();
  modal = null;
  document.body.style.overflow = "";
  opener?.focus();
}
function openModal(from) {
  closeModal();
  opener = from || document.activeElement;
  // a new email account gets its name just after the sign-in event, so draw the nav again once the card is done
  const card = signInCard({ auth, area: "site", onClose: closeModal, onSignedIn: (user) => { closeModal(); rememberAccount("site", user); render(user); } });
  modal = make("div", { className: "ssa-modal" }, card.el);
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
  document.body.append(modal);
  document.body.style.overflow = "hidden";
  card.focus();
}
window.safeshelfSignIn = () => openModal();

// The nav: "Sign in", or the person's face with the account menu
let slot = null;
let menuOpen = () => {};
document.addEventListener("click", (e) => { if (!slot?.contains(e.target)) menuOpen(false); });
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (modal) closeModal();
  else menuOpen(false, true);
});
function render(user) {
  slot?.remove();
  menuOpen = () => {};
  if (!user) {
    const button = make("button", { type: "button", className: "btn btn-ghost btn-sm acct-in", textContent: "Sign in" });
    button.onclick = () => openModal(button);
    slot = button;
  } else {
    const guest = user.isAnonymous;
    const name = guest ? "Guest" : user.displayName || user.email || "Signed in";
    const face = user.photoURL ? make("img", { src: user.photoURL, alt: "", referrerPolicy: "no-referrer" })
      : make("span", { textContent: name.trim()[0].toUpperCase() });
    const toggle = make("button", { type: "button", className: `acct-face${guest ? " guest" : ""}`, "aria-haspopup": "menu", "aria-expanded": "false", "aria-label": `Account: ${name}` }, face);
    const out = make("button", { type: "button", role: "menuitem", textContent: "Sign out" });
    out.onclick = () => signOut(auth);
    const left = make("p", { className: "acct-left", textContent: quota.text() });
    const items = [make("div", { className: "acct-who" }, make("b", { textContent: guest ? "Guest" : user.displayName || "Signed in" }),
      make("small", { textContent: guest ? "No account: 1 free check on this browser" : user.email || "" })), left];
    if (guest) {
      const up = make("button", { type: "button", role: "menuitem", className: "acct-up", textContent: "Sign in for 5 checks a day" });
      up.onclick = async () => { await signOut(auth); openModal(toggle); };
      items.push(up);
    }
    items.push(make("a", { href: "shelf.html", role: "menuitem", textContent: "My Shelf" }),
      make("a", { href: "chat.html", role: "menuitem", textContent: "Chat with Eddy" }),
      make("a", { href: "../index.html", role: "menuitem", textContent: "Try it live" }), out);
    const menu = make("div", { className: "acct-menu", role: "menu", hidden: true }, ...items);
    menuOpen = (open, refocus) => {
      if (!open && menu.hidden) return;
      menu.hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
      if (open) left.textContent = quota.text();
      if (refocus) toggle.focus();
    };
    toggle.onclick = (e) => { e.stopPropagation(); menuOpen(menu.hidden); };
    slot = make("div", { className: "acct" }, toggle, menu);
  }
  end?.insertBefore(slot, end.querySelector(".btn-ink, .menu"));
}

onAuthStateChanged(auth, (user) => {
  rememberAccount("site", user);
  quota.load(user);
  window.safeshelfAccount = user ? {
    uid: user.uid, email: user.email, name: user.displayName, guest: user.isAnonymous,
    token: (fresh) => user.getIdToken(fresh),
    left: () => quota.left(), text: () => quota.text(), usedUpText: () => quota.usedUpText(),
    take: () => quota.take(), // resolves true if this check is allowed and counted
  } : null;
  document.documentElement.classList.toggle("signed-in", Boolean(user));
  render(user);
  dispatchEvent(new CustomEvent("safeshelf:account", { detail: window.safeshelfAccount }));
});
quota.onChange(() => dispatchEvent(new CustomEvent("safeshelf:quota", { detail: { left: quota.left(), text: quota.text() } })));
