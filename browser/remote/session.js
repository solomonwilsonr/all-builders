// Sign-in inside the remote browser ("Start a real browser" on the judges' page): the judge's Firebase ID token for
// this one session, written in when the session starts (browser/server.py). The extension never signs in by itself.
const SESSION = __SESSION__;

export class SignInNeeded extends Error {
  constructor(message = "This browser session has ended. Start a new one on the SafeShelf page") { super(message); this.name = "SignInNeeded"; }
}
export const SIGNIN_ORIGINS = [];
export async function idToken() {
  if (SESSION.expiresAt && Date.now() > SESSION.expiresAt) throw new SignInNeeded();
  return SESSION.idToken;
}
export async function account() { return { email: SESSION.email, name: SESSION.name, role: "shopper" }; }
export async function signOut() {}
export async function openSignIn() {}
export async function acceptSession() { throw new Error("Sign-in is handled by the SafeShelf page here"); }
