const assert = require('node:assert/strict');
const { read, el: baseEl, E, vm } = require('./helpers.cjs');
(async () => {
  let fail = true, copied = null, calls = 0;
  const data = { headline: 'Your next steps', steps: [{ title: 'Stop using it', detail: 'Unplug the charger.' }],
    drafts: [{ kind: 'refund_request', to: 'Seller', body: 'Please refund this charger.', how: [], status: 'Draft only' }],
    case_file: { markdown: '# Case' }, label: 'Review before sending' };
  const ctx = vm.createContext({ document: { createElementNS: (_, tag) => new E(tag) },
    navigator: { clipboard: { writeText: async (value) => { copied = value; } } },
    chrome: { runtime: { sendMessage: (message, cb) => { calls++; cb(fail ? { ok: false, error: 'Offline' } : { ok: true, result: { live: true, data } }); } },
      storage: { local: { get: async () => ({ voiceMode: false }) } } } });
  vm.runInContext(read('aftercare.js'), ctx);
  const el = (...args) => { const node = baseEl(...args); node.remove = () => { node.removed = true; }; return node; };
  const panel = ctx.SafeShelfAftercare.afterPanel(el, {}, { url: 'https://example.com/product' });
  const button = panel.kids[2], error = panel.kids[3], out = panel.kids[4];
  assert.equal(calls, 0, 'building the panel does not send a request');
  assert.equal(button.textContent, 'Get next steps');
  await button.onclick();
  assert.equal(button.disabled, false);
  assert.equal(button.textContent, 'Try again');
  assert.equal(error.hidden, false);
  fail = false;
  await button.onclick();
  assert.equal(button.removed, true);
  assert.equal(error.hidden, true);
  assert.equal(panel.kids[1].hidden, true, 'intro folds away after results');
  const draft = out.kids[0].kids.find((n) => n.className === 'draftbox');
  assert.equal(draft.tag, 'details', 'draft starts folded');
  const textarea = draft.kids.find((n) => n.tag === 'textarea');
  textarea.value = 'My edited request';
  const tools = draft.kids.find((n) => n.className === 'tools');
  await tools.kids[0].onclick();
  assert.equal(copied, 'My edited request', 'copy uses the editable draft');
  assert.equal(button.ariaBusy, 'false');
  console.log('ok aftercare: initial card, retry, steps, folded drafts and editable copy');
})().catch((e) => { console.error(e); process.exit(1); });
