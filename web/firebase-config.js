// Firebase web settings for sign-in (project shelf2026-3656b). These are public by design: they name the project,
// they are not a secret. Access is enforced by the API, which checks every ID token (api/app/auth.py).
export const FIREBASE = {
  apiKey: "AIzaSyA48fOA4Q03yPKeMQedWPW-g4bdvpHi9Pc",
  authDomain: "shelf2026-3656b.firebaseapp.com",
  projectId: "shelf2026-3656b",
  appId: "1:705076726028:web:7e1a99e8e3c983463e2129",
};
export const API = "http://localhost:8080";
// Extensions that signin.html may hand a session to. Empty = any (unpacked copies each get their own ID);
// list the published extension's ID here once it has one.
export const EXTENSION_IDS = [];
