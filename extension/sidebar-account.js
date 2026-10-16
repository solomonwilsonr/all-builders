// Session identity is local, so the sidebar works while the app API is offline.
(() => {
  const profile = document.querySelector(".sidebar-account");
  if (!profile) return;
  const name = profile.querySelector(".sidebar-name");
  const email = profile.querySelector(".sidebar-email");
  const avatar = profile.querySelector(".sidebar-avatar");
  const logout = document.createElement("button");
  logout.type = "button";
  logout.className = "sidebar-logout";
  logout.textContent = "Log out";
  const status = document.createElement("span");
  status.className = "sidebar-account-status";
  status.setAttribute("role", "status");
  profile.querySelector(".sidebar-identity").append(logout, status);
  logout.addEventListener("click", async () => {
    logout.disabled = true;
    status.textContent = "";
    try {
      const reply = await chrome.runtime.sendMessage({ type: "safeshelf:signout" });
      if (!reply?.ok) throw new Error(reply?.error || "Couldn't log out. Try again.");
      render(null);
    } catch (err) {
      status.textContent = err.message;
    } finally {
      logout.disabled = false;
    }
  });
  const render = (session) => {
    const signedIn = Boolean(session?.refreshToken);
    const displayName = signedIn ? session.name || session.email?.split("@")[0] || "Signed in" : "";
    name.textContent = displayName;
    name.title = displayName;
    email.textContent = signedIn ? session.email || "" : "";
    email.title = email.textContent;
    avatar.textContent = Array.from(displayName.trim().split(/\s+/).map((part) => Array.from(part)[0]).slice(0, 2)).join("").toUpperCase();
    profile.hidden = !signedIn;
  };
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && changes.session) {
      updated = true;
      render(changes.session.newValue);
    }
  });
  let updated = false;
  chrome.storage.local.get("session").then(({ session }) => {
    if (!updated) render(session);
  }).catch(() => render(null));
})();
