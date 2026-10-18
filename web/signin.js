// The extension's sign-in page. The extension opens signin.html?ext=<its ID>; after Google sign-in this page hands
// the session (ID token and refresh token) to that extension, which keeps it and sends the token on every API call.
// Only an extension whose manifest lists this site under externally_connectable can receive it.
import { requireSignIn } from "./auth.js?v=20261018u";
import { EXTENSION_IDS } from "./firebase-config.js";

const ext = new URLSearchParams(location.search).get("ext");
const title = document.getElementById("title");
const status = document.getElementById("status");
const done = (heading, text) => { title.textContent = heading; status.textContent = text; };

const user = await requireSignIn();
if (!ext) {
  location.replace("index.html");
} else if (EXTENSION_IDS.length && !EXTENSION_IDS.includes(ext)) {
  done("This sign-in link isn't from SafeShelf", "Open sign-in from the SafeShelf extension's menu instead.");
} else if (!globalThis.chrome?.runtime?.sendMessage) {
  done("The extension can't be reached", "Open this page from the SafeShelf extension in Chrome. If it is installed, reload it on chrome://extensions and try again.");
} else {
  const session = { type: "safeshelf:session", idToken: await user.getIdToken(true), refreshToken: user.refreshToken, email: user.email, name: user.displayName };
  chrome.runtime.sendMessage(ext, session, (res) => {
    if (chrome.runtime.lastError || !res?.ok) {
      done("The extension didn't take the sign-in", res?.error || "Reload the SafeShelf extension on chrome://extensions, then sign in from its menu again.");
    } else {
      done("You're signed in", `The SafeShelf extension now checks products as ${user.email} (${res.role}). This tab closes by itself.`);
    }
  });
}
