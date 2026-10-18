// Home page: the Ask Eddy example questions and the FAQ chat. The rest (menu, product tabs, agent code) is site.js.
(() => {
  const $ = (id) => document.getElementById(id);
  const row = (code, tag, cls, note) => `<div class="r"><code>${code}</code><span class="tag ${cls}">${tag}</span><small>${note}</small></div>`;

  // Ask Eddy: each example question swaps the answer and the records behind it
  const ASK = {
    child: { q: "Is this charger safe for my child's room?", lang: "English", ids: "EV-201 · EV-207",
      a: "<b>Not yet.</b> 9 reports of the USB-C port overheating are under review. Keep it out of children's reach until the review is done.",
      rows: [row("EV-201 · review photo", "REVIEW", "warn", "USB-C port overheating, buyer photo"), row("EV-207 · 9 reports", "REVIEW", "warn", "heat reports from separate buyers"), row("Recalls · 8 regions", "NONE", "ok", "no recall for this exact model")] },
    seller: { q: "Is the seller authorised?", lang: "English", ids: "EV-114",
      a: "<b>No.</b> MegaDealz24 is not on the brand's list of sellers, and the shop opened 19 days ago. The photos are copied from the official listing.",
      rows: [row("EV-114 · brand seller list", "FLAG", "flag", "MegaDealz24 not listed"), row("website_age", "FLAG", "flag", "registered 19 days ago"), row("copied_photos", "FLAG", "flag", "matches the official listing")] },
    hindi: { q: "विक्रेता अधिकृत है?", lang: "हिन्दी", ids: "EV-114",
      a: "<b>नहीं।</b> MegaDealz24 ब्रांड की विक्रेता सूची में नहीं है, और यह दुकान 19 दिन पहले खुली है।",
      rows: [row("EV-114 · brand seller list", "FLAG", "flag", "MegaDealz24 not listed"), row("website_age", "FLAG", "flag", "registered 19 days ago"), row("translation", "MACHINE", "warn", "Gemini, polite form; the record stays in English")] },
    safer: { q: "Is there a safer one?", lang: "English", ids: "EV-207",
      a: "<b>Same model, safer seller:</b> Appario Retail sells the genuine CX-65 at ₹1,349. The 9 heat reports apply to every CX-65, so watch the review either way.",
      rows: [row("Appario Retail · ₹1,349", "EXACT", "ok", "verified seller, same model number"), row("price", "OK", "ok", "in line with the genuine price"), row("EV-207 · 9 reports", "REVIEW", "warn", "applies to the model, not the seller")] },
  };
  const chips = [...document.querySelectorAll("[data-ask]")];
  chips.forEach((c) => c.addEventListener("click", () => {
    const d = ASK[c.dataset.ask];
    chips.forEach((o) => o.setAttribute("aria-pressed", String(o === c)));
    $("ask-q").textContent = d.q;
    $("ask-q").lang = d.lang === "हिन्दी" ? "hi" : "en";
    $("ask-a").innerHTML = d.a;
    $("ask-a").lang = $("ask-q").lang;
    $("ask-lang").textContent = d.lang;
    $("ask-ev-ids").textContent = d.ids;
    $("ask-ev-n").textContent = `${d.rows.length} records`;
    $("ask-rows").innerHTML = d.rows.join("");
    for (const el of [$("ask-a"), $("ask-rows")]) { el.classList.remove("ask-fade"); void el.offsetWidth; el.classList.add("ask-fade"); }
  }));

  // FAQ: a question pill posts the question and Eddy's answer into the chat
  const log = $("faq-log");
  const qs = [...document.querySelectorAll("#faq-qs button")];
  qs.forEach((b) => b.addEventListener("click", () => {
    const [q, a] = b.dataset.a.split("|");
    qs.forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
    log.innerHTML = `<p class="bubble me ask-fade"></p><p class="bubble bot ask-fade">${a}</p>`;
    log.firstChild.textContent = q;
  }));
})();
