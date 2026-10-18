// Sign-in for the extension inside the judges' page: the page around it is already signed in with Google,
// so every API call uses that person's ID token and the widget never shows its own sign-in.
export class SignInNeeded extends Error {
  constructor(message = "Sign in on the SafeShelf page first") { super(message); this.name = "SignInNeeded"; }
}
export const SIGNIN_ORIGINS = [];
const page = () => { try { return window.parent?.SafeShelfDemo || null; } catch (_) { return null; } };
export async function idToken(fresh = false) {
  const p = page();
  if (!p) throw new SignInNeeded("Open this from the SafeShelf judges' page");
  return p.token(fresh);
}
export async function account() { return page()?.who() || null; }
export async function signOut() {}
export async function signedInUid() { return null; } // no shelf sync inside the judges' page (SHELF_SYNC is false)
export async function openSignIn() { page()?.notice?.("You are already signed in on this page."); }
export async function acceptSession() { throw new Error("Sign-in is handled by the judges' page here"); }
