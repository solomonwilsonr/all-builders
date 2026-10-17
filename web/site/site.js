// SafeShelf site: the phone menu, the nav border on scroll, the product tabs, the builder examples and copy buttons.
(() => {
  const top = document.querySelector(".top");
  const menu = document.querySelector(".menu");
  if (menu) menu.addEventListener("click", () => {
    const open = top.classList.toggle("open");
    menu.setAttribute("aria-expanded", String(open));
  });
  const onScroll = () => top && top.classList.toggle("scrolled", scrollY > 8);
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Product tabs: the tab row and the app's side menu both switch the pane
  const tabs = [...document.querySelectorAll(".tab")];
  const pick = (id) => {
    tabs.forEach((t) => t.setAttribute("aria-selected", String(t.id === `tab-${id}`)));
    document.querySelectorAll(".tour .pane").forEach((p) => p.classList.toggle("on", p.id === `pane-${id}`));
    document.querySelectorAll(".tour [data-side]").forEach((s) => s.classList.toggle("on", s.dataset.side === id));
  };
  tabs.forEach((t) => t.addEventListener("click", () => pick(t.id.replace("tab-", ""))));
  document.querySelectorAll(".tour [data-side]").forEach((s) => s.addEventListener("click", () => pick(s.dataset.side)));

  // Builder examples
  const API = "https://safeshelf-api-368488022657.asia-south1.run.app";
  const CODE = {
    mcp: `<span class="c">// any MCP client: tools at /mcp, all read-only</span>
{
  <span class="k">"mcpServers"</span>: {
    <span class="k">"safeshelf"</span>: {
      <span class="k">"url"</span>: <span class="s">"${API}/mcp"</span>,
      <span class="k">"headers"</span>: { <span class="k">"x-api-key"</span>: <span class="s">"YOUR_KEY"</span> }
    }
  }
}

<span class="c">// then your agent can call</span>
<span class="k">check_listing</span>(url=<span class="s">"amazon.in/dp/B0CX65SFC"</span>)
<span class="c">// → copied photos, price, shop age, evidence ids</span>`,
    rest: `<span class="c"># a live investigation, streamed as server-sent events</span>
curl -N -X POST \\
  ${API.replace("https://", "")}\\
  /v1/agent/sessions/stream \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d <span class="s">'{"mode": "investigate",
       "product_id": "unmatched",
       "listing": {"title": "65W Charger CX-65",
                   "price": <span class="n">299</span>, "currency": "INR"}}'</span>`,
    a2a: `<span class="c"># other agents discover SafeShelf here</span>
GET ${API.replace("https://", "")}
    /.well-known/agent-card.json

<span class="c">// and get back its name, skills and endpoint,
// then talk to it agent to agent</span>`,
  };
  const pre = document.getElementById("dev-code");
  const opts = [...document.querySelectorAll(".opt")];
  const showCode = (k) => {
    if (!pre) return;
    pre.innerHTML = CODE[k];
    opts.forEach((o) => o.setAttribute("aria-selected", String(o.dataset.code === k)));
  };
  opts.forEach((o) => o.addEventListener("click", () => showCode(o.dataset.code)));
  showCode("mcp");

  document.querySelectorAll("[data-copy-from]").forEach((b) => b.addEventListener("click", async () => {
    const label = b.textContent;
    try { await navigator.clipboard.writeText(document.getElementById(b.dataset.copyFrom).innerText); b.textContent = "Copied"; }
    catch (_) { b.textContent = "Select and copy"; }
    setTimeout(() => { b.textContent = label; }, 1600);
  }));
})();
