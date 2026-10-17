// How many AI checks the signed-in person has left, kept in Firestore (usage/{uid}_{area}) so it follows the
// account to any device. A guest gets 1 check, ever, on this browser; a Google or email account gets 5 a day
// (UTC days). firestore.rules refuses any write past those limits, so the page can't simply skip the count.
// The API itself stays public: this limits the website and the demo, not someone calling the API directly.
import { doc, getDoc, runTransaction } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js";

export const LIMITS = { guest: 1, account: 5 };
// While we test: every signed-in person (guest too) gets unlimited checks and nothing is counted.
// Set back to false to turn the limits on again.
export const UNLIMITED = true;
const today = () => Math.floor(Date.now() / 86400000);

export function makeQuota(db, area) {
  const flag = `safeshelf-guest-used-${area}`; // a new guest on the same browser doesn't get a second check
  const browserGuestUsed = () => { try { return localStorage.getItem(flag) === "1"; } catch (_) { return false; } };
  const state = { user: null, guest: false, used: 0, ready: false };
  const listeners = new Set();
  const changed = () => listeners.forEach((f) => f(api));
  const ref = () => doc(db, "usage", `${state.user.uid}_${area}`);
  const limit = () => (state.guest ? LIMITS.guest : LIMITS.account);

  const api = {
    get guest() { return state.guest; },
    get ready() { return state.ready; },
    limit,
    left: () => (!state.user ? 0 : UNLIMITED ? Infinity : Math.max(0, limit() - state.used)),
    onChange(f) { listeners.add(f); return () => listeners.delete(f); },
    /** Load the count for this person (call on every sign-in change). */
    async load(user) {
      Object.assign(state, { user, guest: Boolean(user?.isAnonymous), used: 0, ready: false });
      changed();
      if (!user) return;
      try {
        const snap = await getDoc(ref());
        const d = snap.exists() ? snap.data() : null;
        state.used = state.guest ? (d ? d.used : 0) : d && d.day === today() ? d.used : 0;
      } catch (_) { /* offline or rules not deployed: count from zero, the write below still decides */ }
      if (state.guest && browserGuestUsed()) state.used = LIMITS.guest;
      state.ready = state.user === user;
      changed();
    },
    /** Use one check. Resolves true if it was allowed and counted, false if none are left. */
    async take() {
      if (!api.left()) return false;
      if (UNLIMITED) return true;
      state.used += 1; // shown at once; put back below if Firestore refuses
      changed();
      try {
        const used = await runTransaction(db, async (tx) => {
          const snap = await tx.get(ref());
          const d = snap.exists() ? snap.data() : null;
          if (state.guest) {
            if (d) throw Object.assign(new Error("used"), { code: "permission-denied" });
            tx.set(ref(), { day: 0, used: 1 });
            return 1;
          }
          const next = d && d.day === today() ? d.used + 1 : 1;
          if (next > LIMITS.account) throw Object.assign(new Error("used"), { code: "permission-denied" });
          tx.set(ref(), { day: today(), used: next });
          return next;
        });
        state.used = used;
        if (state.guest) { try { localStorage.setItem(flag, "1"); } catch (_) { /* storage off */ } }
        changed();
        return true;
      } catch (err) {
        state.used = err.code === "permission-denied" ? limit() : Math.max(0, state.used - 1);
        changed();
        if (err.code !== "permission-denied") throw new Error("Couldn't count this check. Check your connection and try again.");
        return false;
      }
    },
    /** One line for the page: what is left and why. */
    text() {
      if (!state.user) return "Sign in to run checks";
      if (UNLIMITED) return "Unlimited checks while we test";
      const n = api.left();
      if (state.guest) return n ? "1 free guest check on this browser" : "Guest check used: sign in for 5 checks a day";
      return n ? `${n} of ${LIMITS.account} checks left today` : "Today's 5 checks are used: more tomorrow";
    },
    /** Why a check was refused, in words for the person. */
    usedUpText() {
      return state.guest ? "Your free guest check is used. Sign in with Google or email to get 5 checks a day."
        : "You've used today's 5 checks. They come back tomorrow (midnight UTC).";
    },
  };
  return api;
}
