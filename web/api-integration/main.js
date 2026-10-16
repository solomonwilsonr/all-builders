'use strict';
const $ = id => document.getElementById(id);
const hosted = 'https://safeshelf-api-368488022657.asia-south1.run.app';
let language = 'curl';
try { const saved = localStorage.getItem('kasauti-builders-theme'); if (['light','dark'].includes(saved)) document.documentElement.dataset.theme = saved; } catch {}
const theme = () => { const dark = document.documentElement.dataset.theme === 'dark'; $('theme').setAttribute('aria-pressed', String(dark)); $('theme').setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode'); };
theme();
$('theme').onclick = () => { document.documentElement.dataset.theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'; theme(); try { localStorage.setItem('kasauti-builders-theme', document.documentElement.dataset.theme); } catch {} };
const quote = value => "'" + value.replace(/'/g, "'\\''") + "'";
function render() {
  $('copy-status').textContent = '';
  const op = $('operation').value;
  $('listing-input').hidden = !['trust','identify'].includes(op);
  $('product-input').hidden = op !== 'safety';
  try {
    const base = new URL($('endpoint').value.trim());
    if (!['http:','https:'].includes(base.protocol) || base.username || base.password || base.search || base.hash || base.pathname !== '/') throw new Error('Enter an HTTP(S) API base URL without a path, credentials, query or fragment.');
    const root = base.origin;
    let path = '/health', title = 'Check the connection', body;
    if (op === 'trust' || op === 'identify') {
      const url = new URL($('listing').value.trim());
      if (!['http:','https:'].includes(url.protocol) || url.username || url.password) throw new Error('Enter a valid HTTP(S) product listing URL.');
      body = {url: url.href}; path = op === 'trust' ? '/v1/listings/trust-check' : '/v1/products/identify'; title = op === 'trust' ? 'Check listing trust' : 'Identify a product';
    }
    if (op === 'safety') { const id = $('product').value.trim(); if (!id) throw new Error('Enter a product ID returned by identification.'); path = `/v1/products/${encodeURIComponent(id)}/safety`; title = 'Read product safety'; }
    const url = root + path, auth = $('auth').checked && op !== 'health', method = body ? 'POST' : 'GET';
    $('example-title').textContent = title;
    $('docs').href = root + '/docs';
    let code;
    if (language === 'curl') {
      const parts = [`curl --fail-with-body --request ${method} ${quote(url)}`, ...(auth ? ['  --header "X-API-Key: $SAFESHELF_API_KEY"'] : []), ...(body ? ["  --header 'Content-Type: application/json'", '  --data ' + quote(JSON.stringify(body))] : [])];
      code = parts.join(' \\\n'); $('filename').textContent = 'Terminal';
    } else if (language === 'javascript') {
      code = `// Node.js 18+ (server-side)\nconst response = await fetch(${JSON.stringify(url)}, {\n  method: ${JSON.stringify(method)},\n  headers: {\n${auth ? '    "X-API-Key": process.env.SAFESHELF_API_KEY,\n' : ''}${body ? '    "Content-Type": "application/json",\n' : ''}  },${body ? '\n  body: JSON.stringify(' + JSON.stringify(body, null, 2).replace(/\n/g,'\n  ') + '),' : ''}\n});\nif (!response.ok) throw new Error(\`HTTP \${response.status}: \${await response.text()}\`);\nconsole.log("Source:", response.headers.get("X-SafeShelf-Source"));\nconsole.log(await response.json());`; $('filename').textContent = 'request.mjs';
    } else {
      code = `# Requires: pip install requests\n${auth ? 'import os\n' : ''}import requests\n\nresponse = requests.${method.toLowerCase()}(\n    ${JSON.stringify(url)},\n${auth ? '    headers={"X-API-Key": os.environ["SAFESHELF_API_KEY"]},\n' : ''}${body ? '    json=' + JSON.stringify(body) + ',\n' : ''}    timeout=150,\n)\nresponse.raise_for_status()\nprint("Source:", response.headers.get("X-SafeShelf-Source"))\nprint(response.json())`; $('filename').textContent = 'request.py';
    }
    $('code').textContent = code; $('error').textContent = ''; $('copy').disabled = false;
    $('auth-help').textContent = op === 'health' ? 'Health is public and does not require an API key.' : auth ? 'Set SAFESHELF_API_KEY to your deployment’s service key. This is separate from a Google Gemini API key.' : 'Enable the key option if your deployment requires X-API-Key.';
  } catch (err) { $('code').textContent = 'Complete the connection settings to generate your request.'; $('error').textContent = err.message; $('copy').disabled = true; }
}
$('endpoint').value = hosted;
$('environment').onchange = () => { const v = $('environment').value; $('endpoint').value = v === 'local' ? 'http://localhost:8080' : v === 'hosted' ? hosted : ''; $('local-note').hidden = v !== 'local'; render(); };
for (const id of ['endpoint','operation','listing','product','auth']) $(id).addEventListener('input', render);
const tabs = [...document.querySelectorAll('[data-language]')];
for (const tab of tabs) {
  tab.onclick = () => { language = tab.dataset.language; for (const t of tabs) { t.setAttribute('aria-selected', String(t === tab)); t.tabIndex = t === tab ? 0 : -1; } $('example-panel').setAttribute('aria-labelledby',tab.id); render(); };
  tab.onkeydown = event => { if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return; event.preventDefault(); const i = tabs.indexOf(tab); const target = tabs[event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (i + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length]; target.click(); target.focus(); };
}
$('copy').onclick = async () => { try { await navigator.clipboard.writeText($('code').textContent); $('copy-status').textContent = 'Request copied.'; } catch { $('copy-status').textContent = 'Select the example and copy it manually.'; } };
render();
