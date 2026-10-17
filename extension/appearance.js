// Shared appearance controller for extension documents and isolated in-page UI: light/dark, plus the Theme settings
// (accent colour, font, icon weight), each written as a data attribute that the stylesheets read.
(() => {
  globalThis.SafeShelfAppearance?.cleanup();
  const media = globalThis.matchMedia?.('(prefers-color-scheme: dark)');
  const hosts = new Set();
  const LOOK = { gradient: ['off','on'], accent: ['blue','lime','mint','sky','lilac','peach','sand'], font: ['geist','system','rounded','serif'], icons: ['regular','light','bold'] };
  let preference = 'system';
  const look = Object.fromEntries(Object.entries(LOOK).map(([k, v]) => [k, v[0]]));
  const resolved = () => preference === 'system' ? (media?.matches ? 'dark' : 'light') : preference;
  const paint = (node) => {
    const set = node.dataset ? (k, v) => { node.dataset[k] = v; } : (k, v) => node.setAttribute(`data-${k}`, v);
    set('theme', resolved());
    for (const key of Object.keys(LOOK)) set(key, look[key]);
  };
  function apply() {
    if (location.protocol === 'chrome-extension:') paint(document.documentElement);
    for (const host of hosts) paint(host);
  }
  const read = (data) => {
    if ('appearance' in data) preference = ['light','dark','system'].includes(data.appearance) ? data.appearance : 'system';
    for (const [key, values] of Object.entries(LOOK)) if (key in data) look[key] = values.includes(data[key]) ? data[key] : values[0];
  };
  function changed(changes, area) {
    if (area !== 'local' || !['appearance', ...Object.keys(LOOK)].some((k) => changes[k])) return;
    read(Object.fromEntries(Object.entries(changes).map(([k, c]) => [k, c.newValue])));
    apply();
  }
  chrome.storage.local.get(['appearance', ...Object.keys(LOOK)], data => { read(data || {}); apply(); });
  media?.addEventListener('change', apply);
  chrome.storage.onChanged.addListener(changed);
  globalThis.SafeShelfAppearance = {
    LOOK,
    register(host) { hosts.add(host); paint(host); },
    cleanup() { media?.removeEventListener('change', apply); chrome.storage.onChanged.removeListener(changed); hosts.clear(); }
  };
})();
