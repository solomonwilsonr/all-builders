// The sign-in card, shared by the judges' demo gate (auth.js) and the website's Sign in button (site/account.js).
// Two panels: Eddy on the pixel sky with sample answers on the left; on the right, three ways in: Google, email and
// password (sign in, create an account, reset the password), or a guest with one free check. "Welcome back" offers
// the last account used here. The card does the Firebase sign-in itself, on the auth object it is given.
import { createUserWithEmailAndPassword, GoogleAuthProvider, sendPasswordResetEmail, signInAnonymously, signInWithEmailAndPassword, signInWithPopup, signInWithRedirect, updateProfile } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";

const css = document.createElement("link");
css.rel = "stylesheet";
css.href = new URL("signin-card.css?v=20261017d", import.meta.url).href;
document.head.append(css);

const EDDY = new URL("site/assets/eddy.png", import.meta.url).href;
const NS = "http://www.w3.org/2000/svg";

const make = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k.includes("-") || k === "role") e.setAttribute(k, v);
    else e[k] = v;
  }
  e.append(...kids.filter((k) => k !== null && k !== undefined));
  return e;
};
const svg = (viewBox, inner) => {
  const s = document.createElementNS(NS, "svg");
  s.setAttribute("viewBox", viewBox);
  s.setAttribute("aria-hidden", "true");
  s.innerHTML = inner;
  return s;
};
const googleMark = () => svg("0 0 48 48", `<path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/>`);
const shield = () => svg("0 0 32 32", `<path d="M4 8a6 6 0 0 1 6-6h12a6 6 0 0 1 6 6v8c0 7-5.5 12-12 14C9.5 28 4 23 4 16z" fill="#0271E4"/><path d="m10.5 16 4 4 7-8" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`);
const guestMark = () => svg("0 0 20 20", `<circle cx="10" cy="7" r="3.2"/><path d="M3.8 17c.8-3.2 3.2-5 6.2-5s5.4 1.8 6.2 5"/>`);

/** The last account signed in on this browser in this area, for "Welcome back". Guests aren't remembered. */
const lastKey = (area) => `safeshelf-last-account-${area}`;
export function lastAccount(area) {
  try { return JSON.parse(localStorage.getItem(lastKey(area))) || null; } catch (_) { return null; }
}
export function rememberAccount(area, user) {
  if (!user || user.isAnonymous) return;
  const provider = user.providerData[0]?.providerId === "password" ? "password" : "google";
  try { localStorage.setItem(lastKey(area), JSON.stringify({ name: user.displayName || "", email: user.email || "", photo: user.photoURL || "", provider })); } catch (_) { /* storage off */ }
}

function problem(err) {
  const code = err?.code || "";
  if (code === "auth/invalid-credential" || code === "auth/wrong-password" || code === "auth/user-not-found") return "Wrong email or password. Try again, or reset your password.";
  if (code === "auth/email-already-in-use") return "That email already has an account. Sign in instead.";
  if (code === "auth/weak-password") return "Use a password of at least 6 characters.";
  if (code === "auth/invalid-email") return "That doesn't look like an email address.";
  if (code === "auth/missing-password") return "Type your password.";
  if (code === "auth/too-many-requests") return "Too many tries. Wait a minute, then try again.";
  if (code === "auth/operation-not-allowed" || code === "auth/admin-restricted-operation") return "This way of signing in isn't turned on yet. Use Google for now.";
  if (code === "auth/unauthorized-domain") return `This address (${location.hostname}) isn't allowed to sign in yet.`;
  if (code === "auth/network-request-failed") return "No connection. Check your internet and try again.";
  return `Sign-in didn't work (${code || err?.message}). Try again.`;
}
const quiet = (err) => ["auth/popup-closed-by-user", "auth/cancelled-popup-request"].includes(err?.code);

/**
 * Builds the card.
 * auth: the Firebase auth to sign in on. area: "site" or "demo" (remembered accounts are per area).
 * allowGuest: show "Continue as guest". redirectOnBlock: fall back to a full-page Google redirect if popups are blocked.
 * onSignedIn(user): called after a sign-in from the card. onClose: adds a close button (the website's modal).
 */
export function signInCard({ auth, area = "site", title, text, kicker, allowGuest = true, redirectOnBlock = true, onSignedIn = () => {}, onClose }) {
  const note = make("p", { className: "ssa-error", role: "alert" });
  const say = (msg, ok = false) => { note.textContent = msg; note.classList.toggle("ok", ok); };
  const busyEls = [];
  const run = async (work) => {
    busyEls.forEach((b) => { b.disabled = true; });
    say("");
    try { const user = await work(); if (user) onSignedIn(user); }
    catch (err) { if (!quiet(err)) say(err.friendly || problem(err)); }
    finally { busyEls.forEach((b) => { b.disabled = false; }); }
  };
  const google = (hint) => run(async () => {
    const p = new GoogleAuthProvider();
    p.setCustomParameters(hint ? { prompt: "select_account", login_hint: hint } : { prompt: "select_account" });
    try { return (await signInWithPopup(auth, p)).user; }
    catch (err) {
      if (err.code !== "auth/popup-blocked") throw err;
      if (redirectOnBlock) { await signInWithRedirect(auth, p); return null; }
      throw Object.assign(err, { friendly: "Allow popups for this page, then choose your Google account again." });
    }
  });

  // email and password: sign in, or create an account (with a name) when "Create an account" is on
  let creating = false;
  const name = make("input", { type: "text", name: "name", autocomplete: "name", placeholder: "Your name", "aria-label": "Your name" });
  const email = make("input", { type: "email", name: "email", autocomplete: "email", required: true, placeholder: "Email", "aria-label": "Email" });
  const password = make("input", { type: "password", name: "password", autocomplete: "current-password", required: true, minLength: 6, placeholder: "Password", "aria-label": "Password" });
  const nameRow = make("div", { className: "ssa-field", hidden: true }, name);
  const submit = make("button", { type: "submit", className: "ssa-btn ssa-primary", textContent: "Sign in" });
  const toggle = make("button", { type: "button", className: "ssa-link", textContent: "Create an account" });
  const forgot = make("button", { type: "button", className: "ssa-link", textContent: "Forgot password?" });
  const setMode = (create) => {
    creating = create;
    nameRow.hidden = !create;
    submit.textContent = create ? "Create account" : "Sign in";
    toggle.textContent = create ? "I have an account" : "Create an account";
    forgot.hidden = create;
    password.autocomplete = create ? "new-password" : "current-password";
    say("");
  };
  toggle.onclick = () => { setMode(!creating); (creating ? name : email).focus(); };
  forgot.onclick = () => {
    if (!email.value.trim()) { say("Type your email first, then press Forgot password."); email.focus(); return; }
    run(async () => { await sendPasswordResetEmail(auth, email.value.trim()); say(`If ${email.value.trim()} has an account, a reset link is on its way.`, true); return null; });
  };
  const form = make("form", { className: "ssa-form", noValidate: true }, nameRow,
    make("div", { className: "ssa-field" }, email), make("div", { className: "ssa-field" }, password), submit,
    make("div", { className: "ssa-links" }, forgot, toggle));
  form.onsubmit = (e) => {
    e.preventDefault();
    if (!email.value.trim()) { say("Type your email."); email.focus(); return; }
    if (!password.value) { say("Type your password."); password.focus(); return; }
    run(async () => {
      if (!creating) return (await signInWithEmailAndPassword(auth, email.value.trim(), password.value)).user;
      const { user } = await createUserWithEmailAndPassword(auth, email.value.trim(), password.value);
      if (name.value.trim()) await updateProfile(user, { displayName: name.value.trim() });
      return user;
    });
  };

  const last = lastAccount(area);
  const right = make("div", { className: "ssa-main" });
  right.append(make("div", { className: "ssa-brand" }, shield(), make("span", { textContent: "SafeShelf" })));
  let first = null;
  if (last?.email) {
    const face = last.photo ? make("img", { src: last.photo, alt: "", referrerPolicy: "no-referrer" }) : make("i", { textContent: (last.name || last.email)[0].toUpperCase() });
    const again = make("button", { type: "button", className: "ssa-btn ssa-last" }, face,
      make("span", {}, make("b", { textContent: `Continue as ${last.name?.split(" ")[0] || last.email}` }), make("small", { textContent: last.provider === "password" ? `${last.email} · password` : last.email })));
    again.onclick = last.provider === "password" ? () => { email.value = last.email; password.focus(); } : () => google(last.email);
    busyEls.push(again);
    first = again;
    right.append(make("h2", { id: "ssa-title", textContent: "Welcome back!" }), make("p", { className: "ssa-sub", textContent: "You previously signed in with:" }), again);
  } else {
    right.append(make("h2", { id: "ssa-title", textContent: title || "Sign in to SafeShelf" }),
      make("p", { className: "ssa-sub", textContent: text || "Check listings, chat with Eddy and keep My Shelf on any device." }));
  }
  const googleBtn = make("button", { type: "button", className: "ssa-btn" }, googleMark(), make("span", { textContent: last?.email ? "Another Google account" : "Continue with Google" }));
  googleBtn.onclick = () => google();
  busyEls.push(googleBtn, submit, forgot, toggle);
  first ||= googleBtn;
  right.append(googleBtn, make("div", { className: "ssa-or" }, make("span", { textContent: "or use email" })), form, note);
  if (allowGuest) {
    const guest = make("button", { type: "button", className: "ssa-btn ssa-guest" }, guestMark(), make("span", { textContent: "Continue as guest" }));
    guest.onclick = () => run(async () => (await signInAnonymously(auth)).user);
    busyEls.push(guest);
    right.append(make("div", { className: "ssa-or" }, make("span", { textContent: "or" })), guest,
      make("p", { className: "ssa-new", textContent: "A guest gets 1 free check on this browser. An account gets 5 checks a day." }));
  }
  right.append(make("p", { className: "ssa-fine", textContent: "SafeShelf sees your name, email and profile photo, nothing else. We never post or shop for you." }));

  const left = make("div", { className: "ssa-art", "aria-hidden": "true" },
    make("p", { className: "ssa-kicker", textContent: kicker || "Welcome to SafeShelf" }),
    make("p", { className: "ssa-head", textContent: "Know before you pay, with Eddy" }),
    make("div", { className: "ssa-stage" },
      make("div", { className: "ssa-pill ssa-red" }, make("i", { textContent: "!" }), make("span", {}, make("b", { textContent: "Recalled in Japan" }), make("small", { textContent: "CAA notice · exact model" }))),
      make("div", { className: "ssa-pill ssa-amber" }, make("i", { textContent: "?" }), make("span", {}, make("b", { textContent: "Careful" }), make("small", { textContent: "3 signals, with sources" }))),
      make("div", { className: "ssa-pill ssa-green" }, make("i", { textContent: "✓" }), make("span", {}, make("b", { textContent: "No recalls found" }), make("small", { textContent: "10 regulators checked" }))),
      make("img", { className: "ssa-eddy", src: EDDY, alt: "" }),
      make("p", { className: "ssa-bubble", textContent: "Hi, I'm Eddy, your safety wingman." })));

  const el = make("section", { className: "ssa", role: "dialog", "aria-modal": "true", "aria-labelledby": "ssa-title" }, left, right);
  if (onClose) {
    const x = make("button", { type: "button", className: "ssa-close", "aria-label": "Close" }, svg("0 0 20 20", `<path d="m5 5 10 10M15 5 5 15"/>`));
    x.onclick = onClose;
    el.append(x);
  }
  return { el, focus: () => first.focus(), say };
}
