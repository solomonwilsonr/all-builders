// The extension's settings when it runs inside the judges' page: the same API the page uses, nothing synced.
const fromPage = (() => { try { return window.parent?.SafeShelfDemo?.api; } catch (_) { return null; } })();
export const API_BASE = fromPage || "https://safeshelf-api-368488022657.asia-south1.run.app";
export const SHELF_SYNC = false;
export const SIGNIN_URL = new URL("signin.html", location.href).href;
export const FIREBASE_API_KEY = "";
