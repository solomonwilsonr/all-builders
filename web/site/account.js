// Google sign-in for the website, the same Firebase project as the judges' page (../auth.js), but optional: the
// site stays readable signed out. The nav gets a "Sign in" button; signed in, it shows the person's photo with a
// menu (name, email, Try it live, Sign out). Other scripts read window.safeshelfAccount and listen for
// "safeshelf:account" (the chat keys My Shelf to the Google account).
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signInWithRedirect, signOut } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { FIREBASE } from "../firebase-config.js";

const auth = getAuth(initializeApp(FIREBASE));
const provider = new GoogleAuthProvider();
provider.setCustomParameters({ prompt: "select_account" });

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

function problem(err) {
  if (err.code === "auth/unauthorized-domain") return `${location.hostname} isn't an authorised sign-in domain yet.`;
  if (err.code === "auth/network-request-failed") return "No connection. Check your internet and try again.";
  return `Sign-in didn't work (${err.code || err.message}).`;
}

async function signIn(button) {
  button.disabled = true;
  try {
    await signInWithPopup(auth, provider);
  } catch (err) {
    if (err.code === "auth/popup-blocked") return signInWithRedirect(auth, provider);
    if (!["auth/popup-closed-by-user", "auth/cancelled-popup-request"].includes(err.code)) button.title = problem(err);
  } finally {
    button.disabled = false;
  }
}

let slot = null;
function render(user) {
  slot?.remove();
  if (!user) {
    const button = make("button", { type: "button", className: "btn btn-ghost btn-sm acct-in", textContent: "Sign in" });
    button.onclick = () => signIn(button);
    slot = button;
  } else {
    const name = user.displayName || user.email || "Signed in";
    const face = user.photoURL
      ? make("img", { src: user.photoURL, alt: "", referrerPolicy: "no-referrer" })
      : make("span", { textContent: name.trim()[0].toUpperCase() });
    const toggle = make("button", { type: "button", className: "acct-face", "aria-haspopup": "menu", "aria-expanded": "false", "aria-label": `Account: ${name}` }, face);
    const out = make("button", { type: "button", role: "menuitem", textContent: "Sign out" });
    out.onclick = () => signOut(auth);
    const menu = make("div", { className: "acct-menu", role: "menu", hidden: true },
      make("div", { className: "acct-who" }, make("b", { textContent: user.displayName || "Signed in" }), make("small", { textContent: user.email || "" })),
      make("a", { href: "chat.html", role: "menuitem", textContent: "Chat with Eddy" }),
      make("a", { href: "../index.html", role: "menuitem", textContent: "Try it live" }),
      out);
    const setOpen = (open) => { menu.hidden = !open; toggle.setAttribute("aria-expanded", String(open)); };
    toggle.onclick = (e) => { e.stopPropagation(); setOpen(menu.hidden); };
    document.addEventListener("click", (e) => { if (!slot?.contains(e.target)) setOpen(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) { setOpen(false); toggle.focus(); } });
    slot = make("div", { className: "acct" }, toggle, menu);
  }
  end?.insertBefore(slot, end.querySelector(".btn-ink, .menu"));
}

onAuthStateChanged(auth, (user) => {
  window.safeshelfAccount = user ? { uid: user.uid, email: user.email, name: user.displayName, token: (fresh) => user.getIdToken(fresh) } : null;
  document.documentElement.classList.toggle("signed-in", Boolean(user));
  render(user);
  dispatchEvent(new CustomEvent("safeshelf:account", { detail: window.safeshelfAccount }));
});
