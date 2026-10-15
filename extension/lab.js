const P = globalThis.SafeShelfPanels;
const $ = (id) => document.getElementById(id);
const el = (tag, props = {}, ...kids) => { const n = Object.assign(document.createElement(tag), props); n.append(...kids); return n; };

const USED = {
  trustCheck: "🛡 Check card", safety: "Check card (Is it safe?) and Product explorer", certifications: "Card → Marks; Explorer",
  relationships: "Card → Copies; Explorer", duplicates: "Card → Copies → Find copies with AI", history: "Card → History; Explorer",
  alternatives: "Card → Safer options; Explorer", product: "Card → Details; Explorer", identify: "Card → Details → How was it identified?",
  report: "Card → Report", addShelfItem: "📚 Save to My Shelf", startAgentSession: "Chat under the result", getEvidence: "Evidence under chat answers",
  caseFile: "Lab → Case file (download)", ownerGuidance: "Lab → Already bought it?",
  catalogScan: "Lab → Catalog scan", trace: "Lab → Investigation trace", bench: "Lab → SafeShelfBench",
};
const NOT_LIVE = "Not live on the SafeShelf API yet. Nothing is shown rather than example data.";

function show(into, v) {
  into.replaceChildren(el("div", { className: "vh", textContent: v.title }),
    ...(v.note ? [el("div", { className: "vnote", textContent: v.note })] : []), ...(v.empty ? [el("div", { className: "vnote", textContent: v.empty })] : []),
    ...v.rows.map((r) => r.heading ? el("div", { className: "vh", textContent: r.heading }) : el("div", { className: "vrow" }, el("span", { className: "i", textContent: r.icon }),
      el("div", {}, el("div", { textContent: r.text }), ...(r.sub ? [el("div", { className: "s", textContent: r.sub })] : []),
        ...(/^https?:/.test(r.link || "") ? [el("a", { href: r.link, target: "_blank", rel: "noopener", textContent: "Open source" })] : [])))));
}

function load(into, op, args, key, onData) {
  into.replaceChildren(el("div", { className: "vnote", textContent: "Loading…" }));
  chrome.runtime.sendMessage({ type: "safeshelf:call", op, args }, (res) => {
    if (!res?.ok) return into.replaceChildren(el("div", { className: "nl", textContent: `Could not load this: ${res?.error || chrome.runtime.lastError?.message}` }));
    if (!res.result.live) return into.replaceChildren(el("div", { className: "nl", textContent: NOT_LIVE }));
    show(into, P[key](res.result.data));
    onData?.(res.result.data);
  });
}

function status() {
  const body = document.querySelector("#status tbody");
  body.replaceChildren(el("tr", {}, el("td", { colSpan: 3, textContent: "Loading…" })));
  chrome.runtime.sendMessage({ type: "safeshelf:status" }, (res) => {
    if (!res?.ok) return body.replaceChildren(el("tr", {}, el("td", { colSpan: 3, textContent: `Could not read /health: ${res?.error || chrome.runtime.lastError?.message}` })));
    const rows = res.result;
    body.replaceChildren(...rows.map((o) => el("tr", {},
      el("td", {}, el("code", { textContent: `${o.method} ${o.path}` })),
      el("td", { className: o.live ? "live" : "notlive", textContent: o.live ? "✅ Live" : "⏳ Not live yet" }),
      el("td", { textContent: USED[o.op] || "" }))));
    $("h-status").textContent = `API status: ${rows.filter((o) => o.live).length} of ${rows.length} endpoints live`;
  });
}

$("refresh").onclick = status;
document.querySelectorAll("[data-op]").forEach((b) => {
  b.onclick = () => {
    const pid = $("pid").value.trim();
    if (!pid) return show($("explore"), { title: "Enter a product ID first", rows: [] });
    $("case-dl").hidden = true;
    load($("explore"), b.dataset.op, { product_id: pid }, b.dataset.key, b.dataset.key === "caseFile" ? offerDownload : undefined);
  };
});
// The case file's printable copy, saved as a Markdown file.
function offerDownload(d) {
  const b = $("case-dl");
  b.hidden = !d.markdown;
  b.onclick = () => {
    const a = el("a", { href: URL.createObjectURL(new Blob([d.markdown], { type: "text/markdown" })), download: `safeshelf-case-${d.product_id}.md` });
    a.click();
    URL.revokeObjectURL(a.href);
  };
}
$("bench").onclick = () => load($("bench-out"), "bench", {}, "bench");
$("trace").onclick = () => {
  const id = $("inv").value.trim();
  if (!id) return show($("trace-out"), { title: "Enter an investigation ID first", rows: [] });
  load($("trace-out"), "trace", { investigation_id: id }, "trace");
};
$("scan").onclick = () => {
  const csv = $("csv").value.trim();
  if (!csv) return show($("scan-out"), { title: "Enter the catalog file URL first", rows: [] });
  // TEMP cost guard: the cost of a scan depends on the file, so there is no estimate, only a warning.
  if (!confirm("A catalog scan can use real AI credits, and the cost depends on how many listings the file has. No estimate is possible. Continue?")) return;
  load($("scan-out"), "catalogScan", { csv_url: csv }, "catalogScan");
};
status();
