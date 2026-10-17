// One Firebase app per area, so the website and the judges' demo keep separate sign-ins: signing in on one does
// not sign you in on the other ("site" is the website and the extension hand-off, "demo" is the judges' page).
// On localhost, ?emulators=1 points sign-in and Firestore at the local Firebase emulators (firebase emulators:start).
import { getApp, initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { connectAuthEmulator, getAuth } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { connectFirestoreEmulator, getFirestore } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js";
import { FIREBASE } from "./firebase-config.js";

const local = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
const emulators = local && new URLSearchParams(location.search).has("emulators");

export function firebaseArea(area) {
  const name = area === "demo" ? "demo" : "[DEFAULT]";
  let app;
  try { app = getApp(name); } catch (_) { app = initializeApp(FIREBASE, name === "[DEFAULT]" ? undefined : name); }
  const auth = getAuth(app);
  const db = getFirestore(app);
  if (emulators && !auth.emulatorConfig) {
    connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
    connectFirestoreEmulator(db, "127.0.0.1", 8088);
  }
  return { app, auth, db };
}
