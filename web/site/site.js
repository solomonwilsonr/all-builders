// SafeShelf site: the phone menu, the nav border on scroll, the hero tile motion, the product tabs, the builder examples and copy buttons.
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

  // Hero tiles: each plays its product's check on a loop. data-loop is the last step;
  // an element shows from step data-at until data-off. Typed text and counters run as they appear.
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll(".strip [data-loop]").forEach((tile, n) => {
    const last = Number(tile.dataset.loop);
    const parts = [...tile.querySelectorAll("[data-at]")];
    const typed = [...tile.querySelectorAll("[data-type]")];
    const counts = [...tile.querySelectorAll("[data-count]")];
    let step = -1, timer = null, seen = false;
    const type = (el) => {
      const text = el.dataset.type; let i = 0;
      clearInterval(el._t);
      el._t = setInterval(() => { el.textContent = text.slice(0, ++i); if (i >= text.length) clearInterval(el._t); }, 45);
    };
    const count = (el) => {
      const end = Number(el.dataset.count), unit = el.dataset.unit || "", t0 = performance.now();
      const tick = (t) => { const k = Math.min(1, (t - t0) / 900); el.textContent = Math.round(end * (1 - (1 - k) ** 3)) + unit; if (k < 1) requestAnimationFrame(tick); };
      requestAnimationFrame(tick);
    };
    const show = (s) => {
      step = s;
      parts.forEach((el) => {
        const on = s >= Number(el.dataset.at) && (!el.dataset.off || s < Number(el.dataset.off));
        if (on && !still && !el.classList.contains("on")) {
          if (el.dataset.type) type(el);
          el.querySelectorAll("[data-count]").forEach(count);
          if (el.dataset.count) count(el);
        }
        el.classList.toggle("on", on);
      });
      tile.classList.toggle("typing", tile.querySelector(".dots.on") !== null);
      if (s < 0) { typed.forEach((el) => { clearInterval(el._t); el.textContent = ""; }); counts.forEach((el) => { el.textContent = "0" + (el.dataset.unit || ""); }); }
    };
    if (still) return; // the finished frame is already in the page
    tile.closest(".strip").classList.add("live");
    // one step every 0.9s, hold the answer for 3.5s, then start again
    const next = () => {
      const s = step >= last ? -1 : step + 1;
      show(s);
      timer = setTimeout(next, s === last ? 3500 : s < 0 ? 700 : 900);
    };
    show(-1);
    new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !timer) timer = setTimeout(next, seen ? 300 : 400 + n * 450);
      if (!e.isIntersecting) { clearTimeout(timer); timer = null; }
      seen = seen || e.isIntersecting;
    }).observe(tile);
  });

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
  const terminal = pre?.closest(".tty");
  const prompt = terminal?.querySelector(".tty-prompt");
  const motion = matchMedia("(prefers-reduced-motion: reduce)");
  let terminalRun = 0, currentCode = "mcp", terminalStarted = false;
  let promptText, terminalStatus;
  if (prompt) {
    const text = [...prompt.childNodes].filter((node) => node.nodeType === Node.TEXT_NODE)
      .map((node) => node.textContent).join("");
    [...prompt.childNodes].filter((node) => node.nodeType === Node.TEXT_NODE).forEach((node) => node.remove());
    promptText = document.createElement("span");
    promptText.className = "tty-prompt-text";
    promptText.textContent = text;
    prompt.append(promptText);
    terminalStatus = document.createElement("div");
    terminalStatus.className = "tty-status";
    terminalStatus.setAttribute("role", "status");
    prompt.after(terminalStatus);
  }
  const originalPrompt = promptText?.textContent;
  const showCode = (key) => {
    if (!pre) return;
    pre.innerHTML = CODE[key];
    opts.forEach((option) => option.setAttribute("aria-selected", String(option.dataset.code === key)));
  };
  const settleTerminal = () => {
    ++terminalRun;
    showCode(currentCode);
    if (!terminal) return;
    terminal.classList.remove("tty-composing", "tty-thinking", "tty-streaming");
    pre.removeAttribute("aria-busy");
    if (promptText) promptText.textContent = originalPrompt;
    if (terminalStatus) terminalStatus.textContent = "Example ready · read-only tools";
  };
  const streamTerminal = async (element, token, duration) => {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push({ node: walker.currentNode, text: Array.from(walker.currentNode.textContent) });
    const total = nodes.reduce((sum, item) => sum + item.text.length, 0);
    nodes.forEach(({ node }) => node.textContent = "");
    const start = performance.now();
    while (token === terminalRun) {
      let count = Math.ceil(Math.min(1, (performance.now() - start) / duration) * total);
      nodes.forEach(({ node, text }) => {
        node.textContent = text.slice(0, Math.max(0, count)).join("");
        count -= text.length;
      });
      if (performance.now() - start >= duration) return;
      await new Promise((resolve) => setTimeout(resolve, 30));
    }
  };
  const playTerminal = async (key) => {
    currentCode = key;
    terminalStarted = true;
    settleTerminal();
    if (!terminal || !promptText || motion.matches || document.hidden) return;
    const token = terminalRun;
    // Keep the finished code's footprint as its highlighted text streams in.
    pre.style.minHeight = `${Math.max(pre.getBoundingClientRect().height, parseFloat(pre.style.minHeight) || 0)}px`;
    pre.setAttribute("aria-busy", "true");
    terminal.classList.add("tty-composing");
    terminalStatus.textContent = "Typing example prompt…";
    await streamTerminal(promptText, token, 1200);
    if (token !== terminalRun) return;
    terminal.classList.remove("tty-composing");
    terminal.classList.add("tty-thinking");
    terminalStatus.textContent = "Preparing example response";
    await new Promise((resolve) => setTimeout(resolve, 800));
    if (token !== terminalRun) return;
    terminal.classList.remove("tty-thinking");
    terminal.classList.add("tty-streaming");
    terminalStatus.textContent = `Showing ${key.toUpperCase()} example…`;
    await streamTerminal(pre, token, 2600);
    if (token !== terminalRun) return;
    settleTerminal();
  };
  opts.forEach((option) => option.addEventListener("click", () => playTerminal(option.dataset.code)));
  showCode("mcp");
  if (terminalStatus) terminalStatus.textContent = "Example ready · read-only tools";
  if (terminal && "IntersectionObserver" in window) {
    const terminalObserver = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      if (!terminalStarted) playTerminal(currentCode);
      terminalObserver.disconnect();
    }, { threshold: .3 });
    terminalObserver.observe(terminal);
  }
  motion.addEventListener("change", () => { if (motion.matches) settleTerminal(); });
  document.addEventListener("visibilitychange", () => { if (document.hidden) settleTerminal(); });

  document.querySelectorAll("[data-copy-from]").forEach((b) => b.addEventListener("click", async () => {
    const label = b.textContent;
    try { await navigator.clipboard.writeText(document.getElementById(b.dataset.copyFrom).innerText); b.textContent = "Copied"; }
    catch (_) { b.textContent = "Select and copy"; }
    setTimeout(() => { b.textContent = label; }, 1600);
  }));
})();
