// The signed-in person, kept by the background worker. Nothing in SafeShelf works without a sign-in: the API refuses
// Sign-in happens on the local SafeShelf page (SIGNIN_URL),
// which hands the session to this extension (manifest "externally_connectable"); the refresh token stays in this
// browser's extension storage and an ID token (one hour long) goes with every API call.
import { FIREBASE_API_KEY, SIGNIN_URL } from "./config.js";

export class SignInNeeded extends Error {
  constructor(message = "Sign in to SafeShelf first: click the SafeShelf icon in the toolbar, then Sign in with Google") {
    super(message);
    this.name = "SignInNeeded";
  }
}

// Pages that may hand over a session: the sign-in page, and the judges' page served locally (make web).
export const SIGNIN_ORIGINS = [...new Set([new URL(SIGNIN_URL).origin, "https://shelf2026-3656b.web.app", "https://shelf2026-3656b.firebaseapp.com", "http://localhost:8095"])];

const load = async () => (await chrome.storage.local.get("session")).session || null;
const save = (session) => chrome.storage.local.set({ session });
const expiryOf = (jwt) => {
  try { return JSON.parse(atob(jwt.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))).exp * 1000; } catch (_) { return 0; }
};

export async function signOut() {
  await chrome.storage.local.remove("session");
}

export async function openSignIn() {
  await chrome.tabs.create({ url: `${SIGNIN_URL}?ext=${encodeURIComponent(chrome.runtime.id)}` });
}

// A valid ID token for the API; renews it a minute before it runs out (or now, with fresh: the API refused the
// old one, or an admin just changed the person's role). One renewal at a time.
let renewing = null;
export async function idToken(fresh = false) {
  const s = await load();
  if (!s?.refreshToken) throw new SignInNeeded();
  if (!fresh && s.idToken && s.expiresAt - Date.now() > 60_000) return s.idToken;
  renewing ||= renew(s).finally(() => { renewing = null; });
  return renewing;
}

async function renew(s) {
  const res = await fetch(`https://securetoken.googleapis.com/v1/token?key=${encodeURIComponent(FIREBASE_API_KEY)}`, {
    method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ grant_type: "refresh_token", refresh_token: s.refreshToken }), signal: AbortSignal.timeout(15000) });
  if ([400, 401, 403].includes(res.status)) { // revoked, expired or the account was disabled
    await signOut();
    throw new SignInNeeded("Your SafeShelf sign-in has ended. Click the SafeShelf icon in the toolbar to sign in again");
  }
  if (!res.ok) throw new Error(`SafeShelf couldn't renew your sign-in (${res.status}). Try again in a minute`);
  const t = await res.json();
  await save({ ...s, idToken: t.id_token, refreshToken: t.refresh_token, expiresAt: Date.now() + Number(t.expires_in) * 1000 });
  return t.id_token;
}

// A Firebase session handed over by our allowed sign-in page is stored without contacting the app API.
// Decoded claims are display information only; the API still verifies signatures and permissions on every call.
export async function acceptSession({ idToken: token, refreshToken, name, email }) {
  if (typeof token !== "string" || typeof refreshToken !== "string" || !refreshToken.trim()) throw new Error("That wasn't a SafeShelf sign-in");
  let claims;
  try {
    claims = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
  } catch (_) { throw new Error("That wasn't a SafeShelf sign-in"); }
  const expiresAt = expiryOf(token);
  if (!claims.sub || !Number.isFinite(expiresAt) || expiresAt <= Date.now()) throw new Error("Your sign-in has expired or is not valid. Sign in again.");
  const who = { uid: claims.sub, email: claims.email || email, name: name || claims.name,
    role: ["shopper", "business", "admin"].includes(claims.role) ? claims.role : "shopper" };
  await save({ idToken: token, refreshToken, expiresAt, ...who });
  return who;
}

// The signed-in person's Firebase uid (My Shelf is kept under it in Firestore), or null when signed out.
export async function signedInUid() {
  return (await load())?.uid || null;
}

// The locally stored Firebase profile; no app API call is needed.
export async function account() {
  const s = await load();
  return s ? { email: s.email, name: s.name, role: s.role } : null;
}
