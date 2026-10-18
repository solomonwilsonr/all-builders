// API docs (api.html): live status, the three-step quick start with real runs, and the endpoint reference built
// from api-endpoints.json (made from contracts/openapi.yaml by web/build_api_docs.py).
(() => {
  const API = "https://safeshelf-api-368488022657.asia-south1.run.app";
  const $ = (s, el = document) => el.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const paint = (json) => esc(json)
    .replace(/(&quot;[^&]*?&quot;)(\s*:)/g, '<span class="k">$1</span>$2')
    .replace(/:\s(&quot;.*?&quot;)/g, ': <span class="s">$1</span>')
    .replace(/:\s(-?\d+(\.\d+)?|true|false|null)/g, ': <span class="n">$1</span>');
  const pretty = (v) => JSON.stringify(v, null, 2);

  const copy = async (button, text) => {
    const label = button.textContent;
    try { await navigator.clipboard.writeText(text); button.textContent = "Copied"; }
    catch (_) { button.textContent = "Select and copy"; }
    setTimeout(() => { button.textContent = label; }, 1600);
  };
  document.querySelectorAll("[data-copy-text]").forEach((b) => b.addEventListener("click", () => copy(b, b.dataset.copyText)));

  // --- live status ---------------------------------------------------------------------------------------------
  const live = $("#live");
  const started = performance.now();
  fetch(API + "/health").then((r) => r.json()).then((body) => {
    const ms = Math.round(performance.now() - started);
    live.className = "api-live is-up";
    live.lastChild.textContent = `Live · ${(body.real_endpoints || []).length} engine endpoints · ${ms} ms`;
  }).catch(() => { live.className = "api-live is-down"; live.lastChild.textContent = "Not reachable from this network"; });

  // --- quick start ---------------------------------------------------------------------------------------------
  const LISTING = { url: "https://example-deals-store.test/65w-charger", title: "65W Super Fast Charger - Kelvo CX-65 Original",
    price: 299, currency: "INR", seller: "MegaDealz24" };
  const STEPS = {
    health: { note: "Check the API is up and running the real engine (mock: false).", method: "GET", path: "/health" },
    trust: { note: "A fake shop selling a Rs 1,399 charger for Rs 299. Expect flags for price, website age and hidden AI instructions.",
      method: "POST", path: "/v1/listings/trust-check", body: LISTING },
    stream: { note: "The full investigation, streamed step by step (about 10 s). Uses Gemini, so it counts toward the rate limit.",
      method: "POST", path: "/v1/agent/sessions/stream", body: { mode: "investigate", product_id: "unmatched", listing: LISTING }, sse: true },
  };
  const snippet = (lang, { method, path, body, sse }) => {
    const json = body ? pretty(body) : "";
    if (lang === "curl") {
      const lines = [`curl ${sse ? "-N " : ""}${method === "GET" ? "" : "-X POST "}${API}${path}`];
      if (body) lines.push(`  -H 'content-type: application/json'`, `  -d '${json.replace(/\n/g, "\n     ")}'`);
      return `<span class="c"># ${method} ${path}</span>\n` + esc(lines.join(" \\\n"));
    }
    if (lang === "js") {
      const opts = body ? `, {\n  method: "POST",\n  headers: { "content-type": "application/json" },\n  body: JSON.stringify(${json.replace(/\n/g, "\n  ")}),\n}` : "";
      const read = sse
        ? `const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();\nfor (;;) {\n  const { value, done } = await reader.read();\n  if (done) break;\n  console.log(value);  // "data: {...}" lines: open, step, verdict, done\n}`
        : `console.log(await res.json());`;
      return `<span class="c">// ${method} ${path}</span>\n` + esc(`const res = await fetch("${API}${path}"${opts});\n${read}`);
    }
    const py = body
      ? `res = requests.post(\n    "${API}${path}",\n    json=${json.replace(/true/g, "True").replace(/false/g, "False").replace(/null/g, "None").replace(/\n/g, "\n    ")},${sse ? "\n    stream=True," : ""}\n)`
      : `res = requests.get("${API}${path}")`;
    const read = sse ? `for line in res.iter_lines():\n    if line.startswith(b"data:"):\n        print(line[5:].decode())` : `print(res.json())`;
    return `<span class="c"># ${method} ${path}</span>\n` + esc(`import requests\n\n${py}\n${read}`);
  };

  let step = "health", lang = "curl", running = null;
  const code = $("#step-code"), out = $("#step-out"), status = $("#step-status"), run = $("#step-run");
  const show = () => {
    code.innerHTML = snippet(lang, STEPS[step]);
    $("#step-note em").textContent = STEPS[step].note;
    document.querySelectorAll("[data-step]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.step === step)));
    document.querySelectorAll("[data-lang]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.lang === lang)));
  };
  document.querySelectorAll("[data-step]").forEach((b) => b.addEventListener("click", () => {
    step = b.dataset.step; out.hidden = true; status.textContent = ""; running?.abort(); show();
  }));
  document.querySelectorAll("[data-lang]").forEach((b) => b.addEventListener("click", () => { lang = b.dataset.lang; show(); }));

  const summarise = (event) => {
    const r = event.result || event;
    if (event.type === "step") return `step     ${event.label || event.tool || event.name || ""} ${event.summary || event.text || ""}`.trim();
    if (event.type === "verdict" || event.type === "done") {
      const v = r.verdict || event.verdict || {};
      return `${event.type.padEnd(8)} safe=${v.safe} real=${v.real} overall=${v.overall}\n` +
        (v.reasons || []).map((x) => `         · ${x.text}`).join("\n");
    }
    return `${(event.type || "event").padEnd(8)} ${JSON.stringify(event).slice(0, 140)}`;
  };
  run.addEventListener("click", async () => {
    const s = STEPS[step];
    running?.abort(); running = new AbortController();
    out.hidden = false; out.textContent = ""; status.textContent = "Sending…";
    const t0 = performance.now();
    try {
      const res = await fetch(API + s.path, { method: s.method, signal: running.signal,
        headers: s.body ? { "content-type": "application/json" } : {}, body: s.body ? JSON.stringify(s.body) : undefined });
      if (!s.sse || !res.ok) {
        const text = await res.text();
        let body; try { body = pretty(JSON.parse(text)); } catch (_) { body = text; }
        out.innerHTML = paint(body);
      } else {
        const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
        let buffer = "";
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += value;
          const blocks = buffer.split("\n\n"); buffer = blocks.pop();
          for (const block of blocks) {
            const data = block.split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5)).join("\n");
            if (!data) continue;
            try { out.textContent += `${((performance.now() - t0) / 1000).toFixed(1).padStart(5)}s  ${summarise(JSON.parse(data))}\n`; }
            catch (_) { out.textContent += data + "\n"; }
            out.scrollTop = out.scrollHeight;
          }
        }
      }
      status.textContent = `${res.status} · ${Math.round(performance.now() - t0)} ms`;
    } catch (e) {
      if (e.name !== "AbortError") status.textContent = `Failed: ${e.message}`;
    }
  });
  show();

  // --- reference -----------------------------------------------------------------------------------------------
  const ops = $("#ops"), groups = $("#groups"), filter = $("#filter");
  let data = null;
  const ACCESS = { public: "", "reviewer key": "amber", "developer key": "blue", "internal key": "grey" };

  const urlFor = (op, el) => {
    let path = op.path;
    const query = new URLSearchParams();
    op.params.forEach((p) => {
      const input = el?.querySelector(`[data-param="${p.name}"]`);
      const value = input ? input.value.trim() : (p.default || "");
      if (p.in === "path") path = path.replace(`{${p.name}}`, encodeURIComponent(value || `{${p.name}}`));
      else if (p.in === "query" && value) query.set(p.name, value);
    });
    return API + path + (query.size ? `?${query}` : "");
  };
  const curlFor = (op, el) => {
    const parts = [`curl ${op.method === "GET" ? "" : `-X ${op.method} `}'${urlFor(op, el)}'`];
    if (op.access !== "public") parts.push(`  -H "x-api-key: $SAFESHELF_API_KEY"`);
    if (op.request) parts.push(`  -H 'content-type: application/json'`, `  -d '${JSON.stringify(op.request)}'`);
    return parts.join(" \\\n");
  };

  const opHtml = (op) => {
    const inputs = op.params.filter((p) => p.in !== "header");
    return `<details class="api-op" id="op-${op.id}" data-text="${esc(`${op.method} ${op.path} ${op.summary} ${op.id}`.toLowerCase())}">
      <summary><span class="op-m ${op.method}">${op.method}</span><span class="op-p">${esc(op.path)}</span><span class="op-s">${esc(op.summary)}</span>
        <span class="op-b">${op.runnable ? '<span class="tag api-run-tag">RUN</span>' : ""}${op.access !== "public" ? `<span class="pill ${ACCESS[op.access]}">${op.access}</span>` : ""}</span></summary>
      <div class="api-body">
        <p>${esc(op.description && op.description !== op.summary ? op.description : op.summary)}</p>
        ${op.params.length ? `<div><h4>Parameters</h4><div class="tbl"><table><thead><tr><th>Name</th><th>In</th><th>About</th></tr></thead><tbody>${op.params.map((p) =>
          `<tr><td class="ep">${esc(p.name)}${p.required ? " *" : ""}</td><td>${p.in}</td><td>${esc(p.description || "")}</td></tr>`).join("")}</tbody></table></div></div>` : ""}
        ${inputs.length && op.runnable ? `<div class="api-fields">${inputs.map((p) =>
          `<label>${esc(p.name)}<input data-param="${esc(p.name)}" value="${esc(p.default || "")}" placeholder="${p.required ? "required" : "optional"}"></label>`).join("")}</div>` : ""}
        <div class="two">
          <div><h4>Request</h4><pre class="code" data-curl></pre></div>
          <div><h4>${op.example ? "Example answer" : "Answer"}</h4><pre class="code" data-out>${op.example ? paint(op.example) : '<span class="c">// see the interactive OpenAPI page</span>'}</pre></div>
        </div>
        <div class="api-actions">${op.runnable ? '<button class="btn btn-blue btn-sm" type="button" data-run>Run live</button>' : ""}<button class="copy-btn" type="button" data-copy>Copy cURL</button><span data-status role="status"></span></div>
      </div></details>`;
  };

  const render = () => {
    const q = filter.value.trim().toLowerCase();
    let shown = 0;
    ops.querySelectorAll(".api-op").forEach((el) => {
      const hit = !q || el.dataset.text.includes(q);
      el.hidden = !hit; shown += hit;
    });
    ops.querySelectorAll(".api-group").forEach((g) => { g.hidden = !g.querySelector(".api-op:not([hidden])"); });
    groups.querySelectorAll("a").forEach((a) => {
      const g = $(a.getAttribute("href"));
      a.hidden = g.hidden;
      a.querySelector("small").textContent = g.querySelectorAll(".api-op:not([hidden])").length;
    });
    $("#ops-empty").hidden = shown > 0;
  };

  fetch("api-endpoints.json?v=20261018a").then((r) => r.json()).then((d) => {
    data = d;
    document.querySelectorAll("[data-count]").forEach((el) => { el.textContent = d.count; });
    groups.innerHTML = d.groups.map((g) => `<a href="#g-${g.id}">${esc(g.title)}<small>${g.ops.length}</small></a>`).join("");
    ops.innerHTML = d.groups.map((g) => `<section class="api-group" id="g-${g.id}"><h3 class="display">${esc(g.title)}</h3><p>${esc(g.blurb)}</p>${g.ops.map(opHtml).join("")}</section>`).join("") +
      '<p class="api-empty" id="ops-empty" hidden>No endpoint matches. Try "recall", "safety" or "POST".</p>';
    const byId = Object.fromEntries(d.groups.flatMap((g) => g.ops).map((op) => [op.id, op]));
    ops.querySelectorAll(".api-op").forEach((el) => {
      const op = byId[el.id.slice(3)];
      const curl = el.querySelector("[data-curl]");
      const refresh = () => { curl.textContent = curlFor(op, el); };
      refresh();
      el.querySelectorAll("[data-param]").forEach((i) => i.addEventListener("input", refresh));
      el.querySelector("[data-copy]").addEventListener("click", (e) => copy(e.currentTarget, curlFor(op, el)));
      el.querySelector("[data-run]")?.addEventListener("click", async () => {
        const st = el.querySelector("[data-status]"), output = el.querySelector("[data-out]");
        st.textContent = "Sending…";
        const t0 = performance.now();
        try {
          const res = await fetch(urlFor(op, el), { method: op.method,
            headers: op.request ? { "content-type": "application/json" } : {}, body: op.request ? JSON.stringify(op.request) : undefined });
          const text = await res.text();
          let body; try { body = pretty(JSON.parse(text)); } catch (_) { body = text; }
          const lines = body.split("\n");
          output.innerHTML = paint(lines.slice(0, 120).join("\n") + (lines.length > 120 ? "\n  …" : ""));
          output.previousElementSibling.textContent = `Live answer (${res.status})`;
          st.textContent = `${res.status} · ${Math.round(performance.now() - t0)} ms`;
        } catch (e) { st.textContent = `Failed: ${e.message}`; }
      });
    });
    filter.addEventListener("input", render);
    render();
    if (location.hash.startsWith("#op-")) { const el = $(location.hash); if (el) { el.open = true; el.scrollIntoView(); } }
  }).catch(() => { ops.innerHTML = '<p class="api-empty">The endpoint list didn\'t load. The interactive OpenAPI page has every endpoint: <a href="' + API + '/docs">' + API + "/docs</a></p>"; });

  // Mark the group on screen in the side list.
  const spy = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (e.isIntersecting) groups.querySelectorAll("a").forEach((a) => a.classList.toggle("on", a.getAttribute("href") === `#${e.target.id}`));
  }), { rootMargin: "-30% 0px -60% 0px" });
  new MutationObserver(() => ops.querySelectorAll(".api-group").forEach((g) => spy.observe(g))).observe(ops, { childList: true });
})();
