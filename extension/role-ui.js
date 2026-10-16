// Fail closed while role verification is pending, including direct Lab URLs.
(() => {
  let version = 0;
  const root = document.documentElement;
  const status = document.createElement('p');
  status.className = 'role-verification-status';
  status.setAttribute('role', 'status');
  status.hidden = true;
  (document.querySelector('.sidebar-footer, #app-view') || document.body).append(status);
  async function refresh() {
    const current = ++version;
    root.dataset.role = 'user';
    status.hidden = true;
    const notice = document.getElementById('admin-access-notice');
    if (notice) notice.textContent = 'Verifying administrator access…';
    try {
      const reply = await chrome.runtime.sendMessage({ type: 'safeshelf:identity' });
      if (current !== version) return;
      if (!reply?.ok) throw new Error(reply?.error || 'Could not verify administrator access.');
      root.dataset.role = reply?.ok && reply.result?.role === 'admin' ? 'admin' : 'user';
      if (notice) notice.textContent = root.dataset.role === 'admin' ? '' : 'Administrator access required. Open My Shelf or Settings to continue.';
    } catch (error) {
      if (current === version) {
        status.textContent = error.message || 'Could not verify administrator access. Reload to try again.';
        status.hidden = false;
        if (notice) notice.textContent = status.textContent;
      }
    }
    if (current === version) document.dispatchEvent(new Event('safeshelf:role'));
  }
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.session) refresh();
  });
  addEventListener('focus', refresh);
  refresh();
})();
