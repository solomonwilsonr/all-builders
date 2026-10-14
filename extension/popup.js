const power = document.getElementById("power");

function show(enabled) {
  power.setAttribute("aria-checked", String(enabled));
  document.getElementById("power-label").textContent = enabled ? "SafeShelf is on" : "SafeShelf is off";
  document.getElementById("power-state").textContent = enabled ? "On" : "Off";
}

chrome.storage.local.get("enabled", ({ enabled }) => show(enabled !== false));

power.addEventListener("click", async () => {
  const { enabled } = await chrome.storage.local.get("enabled");
  const next = enabled === false; // flip
  await chrome.storage.local.set({ enabled: next });
  show(next);
});

document.getElementById("shelf").addEventListener("click", () => {
  chrome.tabs.create({ url: chrome.runtime.getURL("shelf.html") });
  window.close();
});

// --- TEMP cost guard ---
const guardBtn = document.getElementById("guard");
function showGuard(on) {
  guardBtn.setAttribute("aria-checked", String(on));
  document.getElementById("guard-state").textContent = on ? "On" : "Off";
}
function showSpend({ total = 0, calls = 0 } = {}) {
  document.getElementById("spend").textContent = `Estimated AI spend: ₹${total.toFixed(2)} (${calls} request${calls === 1 ? "" : "s"})`;
}
chrome.storage.local.get(["costGuard", "spend"], ({ costGuard, spend }) => { showGuard(costGuard !== false); showSpend(spend); });
guardBtn.addEventListener("click", async () => {
  const { costGuard } = await chrome.storage.local.get("costGuard");
  const next = costGuard === false;
  await chrome.storage.local.set({ costGuard: next });
  showGuard(next);
});
document.getElementById("spend-reset").addEventListener("click", async () => {
  await chrome.storage.local.set({ spend: { total: 0, calls: 0 } });
  showSpend();
});
chrome.storage.onChanged.addListener((c) => { if (c.spend) showSpend(c.spend.newValue); });

document.getElementById("lab").addEventListener("click", () => {
  chrome.tabs.create({ url: chrome.runtime.getURL("lab.html") });
  window.close();
});
