// The sign-in card, shared by the judges' page gate (auth.js) and the website's Sign in button (site/account.js).
// Two panels: Eddy on the pixel sky with sample answers on the left; on the right, "Continue with Google" (it
// signs in or creates the account), and "Welcome back" with a one-click button for the last account used here.
const css = document.createElement("link");
css.rel = "stylesheet";
css.href = new URL("signin-card.css?v=20261017c", import.meta.url).href;
document.head.append(css);

const EDDY = new URL("site/assets/eddy.png", import.meta.url).href;
const LAST = "safeshelf-last-account";
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

/** The last account signed in on this browser, for "Welcome back". */
export function lastAccount() {
  try { return JSON.parse(localStorage.getItem(LAST)) || null; } catch (_) { return null; }
}
export function rememberAccount(user) {
  try { localStorage.setItem(LAST, JSON.stringify({ name: user.displayName || "", email: user.email || "", photo: user.photoURL || "" })); } catch (_) { /* storage off */ }
}

/**
 * Builds the card. onGoogle(email?) starts Google sign-in, with a login hint for the remembered account; it may
 * throw a message to show. onClose, when given, adds a close button (the website); the judges' gate has none.
 */
export function signInCard({ title, text, onGoogle, onClose }) {
  const error = make("p", { className: "ssa-error", role: "alert" });
  const buttons = [];
  const go = (hint) => async () => {
    buttons.forEach((b) => { b.disabled = true; });
    error.textContent = "";
    try { await onGoogle(hint); } catch (err) { error.textContent = err?.message || String(err); }
    finally { buttons.forEach((b) => { b.disabled = false; }); }
  };

  const last = lastAccount();
  const right = make("div", { className: "ssa-main" });
  right.append(make("div", { className: "ssa-brand" }, shield(), make("span", { textContent: "SafeShelf" })));
  if (last?.email) {
    const face = last.photo ? make("img", { src: last.photo, alt: "", referrerPolicy: "no-referrer" }) : make("i", { textContent: (last.name || last.email)[0].toUpperCase() });
    const again = make("button", { type: "button", className: "ssa-btn ssa-last" }, face,
      make("span", {}, make("b", { textContent: `Continue as ${last.name?.split(" ")[0] || last.email}` }), make("small", { textContent: last.email })));
    again.onclick = go(last.email);
    buttons.push(again);
    right.append(make("h2", { id: "ssa-title", textContent: "Welcome back!" }),
      make("p", { className: "ssa-sub", textContent: "You previously signed in with:" }), again,
      make("div", { className: "ssa-or" }, make("span", { textContent: "Or" })));
  } else {
    right.append(make("h2", { id: "ssa-title", textContent: title || "Sign in to SafeShelf" }),
      make("p", { className: "ssa-sub", textContent: text || "Check listings, chat with Eddy and keep My Shelf on any device." }));
  }
  const google = make("button", { type: "button", className: "ssa-btn" }, googleMark(), make("span", { textContent: last?.email ? "Use another Google account" : "Continue with Google" }));
  google.onclick = go();
  buttons.push(google);
  right.append(google, error,
    make("p", { className: "ssa-new" }, "New to SafeShelf? ", make("b", { textContent: "Continue with Google" }), " creates your account."),
    make("p", { className: "ssa-fine", textContent: "SafeShelf sees your name, email and profile photo, nothing else. We never post or shop for you." }));

  const left = make("div", { className: "ssa-art", "aria-hidden": "true" },
    make("p", { className: "ssa-kicker", textContent: "Welcome to SafeShelf" }),
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
  return { el, focus: () => buttons[0].focus(), setError: (msg) => { error.textContent = msg; } };
}
