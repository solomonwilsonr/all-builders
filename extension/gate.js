// My Shelf, the Lab and Settings are for signed-in people. Until someone signs in (session.js), a sign-in card
// covers the page; it goes away by itself once the sign-in page hands the session to the extension.
// Loaded in <head> without defer, so the page never shows before the check.
(() => {
  const root = document.documentElement;
  root.style.visibility = "hidden";
  let cover = null;

  const show = () => {
    if (cover) return;
    cover = document.createElement("div");
    cover.className = "signin-cover";
    cover.innerHTML = `<style>
      .signin-cover { position:fixed; inset:0; z-index:2147483647; display:grid; place-items:center; padding:16px; visibility:visible;
        background:url(assets/sky.png) center / cover; image-rendering:pixelated; font:16px/1.55 var(--font, "Helvetica Neue", Helvetica, Arial, system-ui, sans-serif); color:var(--ink, #001123); }
      .signin-cover section { image-rendering:auto; max-width:420px; width:100%; padding:30px 28px; border-radius:14px; background:var(--surface, var(--card, #fff)); box-shadow:0 30px 60px rgba(0,17,35,.2); }
      .signin-cover section::before { content:""; display:block; width:30px; height:30px; margin-bottom:16px; background:var(--shield) center / contain no-repeat; }
      .signin-cover h1 { font-size:24px; font-weight:600; letter-spacing:-.03em; margin:0 0 8px; color:var(--ink, #001123); }
      .signin-cover p { margin:0 0 18px; color:var(--ink-2, var(--muted, #5d6874)); }
      .signin-cover .signin-status { margin:14px 0 0; font-size:14px; }
      .signin-cover .signin-status:empty { display:none; }
      .signin-cover button { font:inherit; font-weight:500; padding:12px 22px; border:0; border-radius:4px; background:var(--action, var(--primary, #0271e4)); color:var(--on-action, var(--on-primary, #fff)); cursor:pointer; }
      .signin-cover button:focus-visible { outline:2px solid var(--action, #0271e4); outline-offset:2px; }
    </style><section role="dialog" aria-modal="true" aria-labelledby="signin-cover-title">
      <h1 id="signin-cover-title">Sign in to use SafeShelf</h1>
      <p>Checks, chat, My Shelf and the Lab are for signed-in people. Use your Google account: SafeShelf sees your name, email and profile photo, nothing else.</p>
      <button type="button">Sign in with Google</button>
      <p class="signin-status" role="status" aria-live="polite"></p></section>`;
    const button = cover.querySelector("button");
    const status = cover.querySelector(".signin-status");
    button.onclick = async () => {
      button.disabled = true;
      status.textContent = "Opening Google sign-in…";
      try {
        const reply = await chrome.runtime.sendMessage({ type: "safeshelf:signin" });
        if (!reply?.ok) throw new Error(reply?.error || "Reload SafeShelf on chrome://extensions and try again.");
        status.textContent = "Complete sign-in in the new tab. If localhost won't open, start the sign-in page with make web.";
      } catch (err) {
        status.textContent = `Couldn't open sign-in. ${err.message}`;
      } finally {
        button.disabled = false;
      }
    };
    document.body.append(cover);
    cover.querySelector("button").focus();
  };

  const check = async () => {
    const { session } = await chrome.storage.local.get("session");
    if (session?.refreshToken) {
      cover?.remove();
      cover = null;
    } else if (document.body) {
      show();
    } else {
      document.addEventListener("DOMContentLoaded", show, { once: true });
    }
    root.style.visibility = "";
  };
  chrome.storage.onChanged.addListener((changes, area) => { if (area === "local" && changes.session) check(); });
  check();
})();
