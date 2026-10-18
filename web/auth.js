// Sign-in for the judges' demo page and the extension hand-off page. Nothing on the page works until the person
// signs in: the page starts hidden (<html class="auth-locked">) and the sign-in card is shown instead (Google, email
// and password, or a guest). The demo has its own sign-in, separate from the website's (firebase-app.js); the
// extension hand-off uses the website's. API calls go through authFetch, which sends the Firebase ID token, and
// `quota` counts the AI checks used (quota.js: a guest gets 1, an account 5 a day).
import { onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { firebaseArea } from "./firebase-app.js?v=20261017v";
import { API } from "./firebase-config.js";
import { makeQuota } from "./quota.js?v=20261018u";
import { rememberAccount, signInCard } from "./signin-card.js?v=20261017v";

export { API };
const root = document.documentElement;
// The extension must receive an account explicitly chosen in this visit, not a cached web login.
const chooseAccount = Boolean(document.querySelector(".handoff"));
const AREA = chooseAccount ? "site" : "demo";
const { auth: fbAuth, db } = firebaseArea(AREA);
export const auth = fbAuth;
export const quota = makeQuota(db, AREA);

let resolveSignedIn;
const signedIn = new Promise((resolve) => { resolveSignedIn = resolve; });
let accountChosen = false;
const make = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k.includes("-") || k === "role") e.setAttribute(k, v); // data-*, aria-*: attributes, not properties
    else e[k] = v;
  }
  e.append(...kids);
  return e;
};

// --- The sign-in card, shown while nobody is signed in ---
let gate = null;
function lock() {
  root.classList.add("auth-locked");
  gate?.remove(); // rebuilt each time, so "Welcome back" shows the latest account
  const card = signInCard({
    auth,
    area: AREA,
    title: root.dataset.gateTitle || "Sign in to the demo",
    text: root.dataset.gateText || "The demo has its own sign-in, separate from your SafeShelf account on the website.",
    kicker: chooseAccount ? "Welcome to SafeShelf" : "SafeShelf · judges' demo",
    allowGuest: !chooseAccount, // the extension needs a real account
    redirectOnBlock: !chooseAccount,
    // a new email account gets its name just after the sign-in event, so show it again once the card is done
    onSignedIn: (user) => { if (chooseAccount) completeSignIn(user); else { rememberAccount(AREA, user); mountAccount(); } },
  });
  gate = make("div", { className: "gate" }, card.el);
  document.body.prepend(gate);
  card.focus();
}

function completeSignIn(user) {
  accountChosen = true;
  rememberAccount(AREA, user);
  root.classList.remove("auth-locked");
  gate?.remove();
  gate = null;
  resolveSignedIn(user);
  if (!chooseAccount) quota.load(user);
  mountAccount();
}

onAuthStateChanged(auth, (user) => {
  if (!user || (chooseAccount && !accountChosen)) {
    quota.load(null);
    return lock();
  }
  completeSignIn(user);
});

/** Resolves with the Firebase user once someone is signed in. */
export const requireSignIn = () => signedIn;

/** fetch() with the signed-in person's ID token. A 401 or 403 asks once more with a fresh token: the old one may
 * have just expired. */
export async function authFetch(url, init = {}) {
  const user = auth.currentUser || (await signedIn);
  const send = async (fresh) => fetch(url, { ...init, headers: { ...init.headers, Authorization: `Bearer ${await user.getIdToken(fresh)}` } });
  const res = await send(false);
  return res.status === 401 || res.status === 403 ? send(true) : res;
}

// Show who is signed in (or "Guest") and the way out; a guest's button reads "Sign in" (to get 5 checks a day).
let account = null;
function mountAccount() {
  if (chooseAccount) return; // the extension hand-off needs only Firebase
  const row = document.querySelector("body > header .brand-row, main .brand-row");
  const user = auth.currentUser;
  if (!row || !user) return;
  account?.remove();
  const out = make("button", { type: "button", className: "link", textContent: user.isAnonymous ? "Sign in" : "Sign out" });
  out.onclick = () => signOut(auth);
  const who = user.isAnonymous ? "Guest" : [user.displayName, user.email].filter(Boolean).join(" · ") || "Signed in";
  account = make("span", { className: "account" }, make("span", { className: "who", textContent: who }), out);
  row.append(account);
}
