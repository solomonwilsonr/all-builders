// Sign-in for every SafeShelf web page: Google sign-in through Firebase Auth. Nothing on a page works until the
// person signs in: the page starts hidden (<html class="auth-locked">) and a sign-in card is shown instead.
// API calls go through authFetch, which sends the Firebase ID token.
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signInWithRedirect, signOut } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { API, FIREBASE } from "./firebase-config.js";
import { rememberAccount, signInCard } from "./signin-card.js?v=20261017u";

export { API };
export const auth = getAuth(initializeApp(FIREBASE));
const provider = new GoogleAuthProvider();
provider.setCustomParameters({ prompt: "select_account" });

let resolveSignedIn;
const signedIn = new Promise((resolve) => { resolveSignedIn = resolve; });

const root = document.documentElement;
// The extension must receive an account explicitly chosen in this visit, not a cached web login.
const chooseAccount = Boolean(document.querySelector(".handoff"));
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
  if (gate) {
    gate.hidden = false;
    return;
  }
  const card = signInCard({
    title: root.dataset.gateTitle,
    text: root.dataset.gateText || "Checks, chat and the agents are for signed-in people.",
    onGoogle: async (hint) => {
      try {
        const result = await signInWithPopup(auth, providerFor(hint));
        if (chooseAccount) completeSignIn(result.user);
      } catch (err) {
        if (err.code === "auth/popup-blocked") {
          if (chooseAccount) throw new Error("Allow popups for this page, then choose your Google account again.");
          return signInWithRedirect(auth, providerFor(hint));
        }
        if (!["auth/popup-closed-by-user", "auth/cancelled-popup-request"].includes(err.code)) throw new Error(signInProblem(err));
      }
    },
  });
  gate = make("div", { className: "gate" }, card.el);
  document.body.prepend(gate);
  card.focus();
}

// Google's account picker, with the remembered account preselected for "Continue as".
function providerFor(hint) {
  if (!hint) return provider;
  const p = new GoogleAuthProvider();
  p.setCustomParameters({ prompt: "select_account", login_hint: hint });
  return p;
}

function signInProblem(err) {
  if (err.code === "auth/unauthorized-domain") return `This address (${location.hostname}) isn't allowed to sign in yet. In the Firebase console, add it under Authentication → Settings → Authorized domains.`;
  if (err.code === "auth/network-request-failed") return "No connection. Check your internet and try again.";
  return `Sign-in didn't work (${err.code || err.message}). Try again.`;
}

function completeSignIn(user) {
  accountChosen = true;
  rememberAccount(user);
  root.classList.remove("auth-locked");
  if (gate) gate.hidden = true;
  resolveSignedIn(user);
  mountAccount();
}

onAuthStateChanged(auth, (user) => {
  if (!user || (chooseAccount && !accountChosen)) return lock();
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

// Show the Firebase profile and sign-out action.
let account = null;
function mountAccount() {
  // The extension handoff needs only Firebase; do not ask the app API for a role on this page.
  if (document.querySelector(".handoff")) return;
  const row = document.querySelector("body > header .brand-row, main .brand-row");
  if (!row || !auth.currentUser) return;
  account?.remove();
  const out = make("button", { type: "button", className: "link", textContent: "Sign out" });
  out.onclick = () => signOut(auth);
  account = make("span", { className: "account" }, make("span", { className: "who", textContent: [auth.currentUser.displayName, auth.currentUser.email].filter(Boolean).join(" · ") || "Signed in" }), out);
  row.append(account);
}
