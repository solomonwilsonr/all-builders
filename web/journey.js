// The judges' page as one journey (steps 1–7): the "Ask Eddy" buttons on the After you buy and If something goes wrong
// cards hand their question to the real chat in step 1 (site/chat.html?embed=1&q=…), so those features are shown by
// the one chat rather than a second copy; the Recall Catalog search in step 5 calls the live API (GET /v1/recalls);
// and the jump bar marks the step on screen. Plain module, no build step. Text is always set as text, never as HTML.
import { API, el } from "./actions.js?v=20261017v";

// --- Ask Eddy: open the chat tab with the card's question typed in ---
function setUpAsk() {
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-ask]");
    if (!b) return;
    const frame = document.getElementById("chatframe");
    const panel = document.getElementById("chat");
    if (!frame || !panel) return;
    frame.dataset.loaded = "1"; // before the tab opens, so it keeps this address instead of the plain chat
    frame.src = `site/chat.html?embed=1&q=${encodeURIComponent(b.dataset.ask)}`;
    document.getElementById("tab-chat")?.click();
    panel.dataset.view = "live";
    panel.querySelector(".live")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

// --- Recall Catalog: search the official notices on the live API ---
const day = (d) => { try { return new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }); } catch (_) { return d; } };
const clip = (t, n) => { const s = String(t || "").replace(/\s+/g, " ").trim(); return s.length > n ? `${s.slice(0, n - 1)}…` : s; };

function setUpRecalls() {
  const form = document.getElementById("rc-form");
  const list = document.getElementById("rc-list");
  const total = document.getElementById("rc-total");
  if (!form || !list) return;
  let run = 0;
  const search = async () => {
    const mine = ++run;
    const q = form.elements.q.value.trim();
    const country = form.elements.country.value;
    const url = new URL(`${API}/v1/recalls`);
    if (q) url.searchParams.set("q", q);
    if (country) url.searchParams.set("country", country);
    url.searchParams.set("per_page", "6");
    total.textContent = "Searching…";
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error(r.status);
      const d = await r.json();
      if (mine !== run) return;
      total.textContent = `${d.total.toLocaleString("en-IN")} notices${q ? ` for “${q}”` : ""}${country ? ` in ${country}` : ""} · showing the newest ${d.recalls.length}`;
      list.replaceChildren(...d.recalls.map((x) => el("li", {},
        el("div", { className: "rc-top" }, el("span", { className: "tag flag", textContent: x.authority }),
          el("small", { textContent: `${x.country} · ${day(x.notice_date)}` })),
        el("b", { textContent: clip(x.title, 110) }),
        el("p", { textContent: clip(x.hazard, 170) }),
        x.url ? el("a", { href: x.url, target: "_blank", rel: "noopener", textContent: "Official notice" }) : null)));
      if (!d.recalls.length) list.replaceChildren(el("li", { className: "muted", textContent: "No notices match. Try a shorter word, such as heater or charger." }));
    } catch (_) {
      if (mine !== run) return;
      total.textContent = "The Recall Catalog could not be reached just now.";
      list.replaceChildren();
    }
  };
  form.addEventListener("submit", (e) => { e.preventDefault(); search(); });
  form.elements.country.addEventListener("change", search);
  search();
}

// --- The jump bar and the seven-step card mark the step on screen ---
function setUpSteps() {
  const links = [...document.querySelectorAll(".jump a, .journey ol a")];
  const sections = [...new Set(links.map((a) => a.hash))].map((h) => document.querySelector(h)).filter(Boolean);
  if (!("IntersectionObserver" in window)) return;
  const seen = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      links.forEach((a) => a.classList.toggle("on", a.hash === `#${e.target.id}`));
      document.querySelector(".jump a.on")?.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }, { rootMargin: "-35% 0px -60% 0px" });
  sections.forEach((s) => seen.observe(s));
}

export function setUpJourney() {
  setUpAsk();
  setUpRecalls();
  setUpSteps();
}
