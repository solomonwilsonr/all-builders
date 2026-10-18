const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { read, el, EXT } = require('./helpers.cjs');
const source = read('content.js');
const code = source.slice(source.indexOf('  const FLAG_COUNTRIES ='), source.indexOf('  const detailsBox ='));
const summary = Function(code + '; return recallSummary;')();
assert.equal(summary(Array.from({length:8}, () => ({mark:'ok'}))).text, 'No recalls found in 8 countries');
assert.equal(summary([{mark:'ok'}, {mark:'skip'}]).text, 'No recalls found in 1 country · 1 unchecked');
assert.equal(summary([{mark:'warn'}]).state, 'warning');
assert.equal(summary([]).state, 'partial');
const placesBlock = Function('el', 'chrome', 'MARKS', code + '; return placesBlock;')(el,
  { runtime: { getURL: (p) => 'chrome-extension://test/' + p } }, { ok: '✓' });
const block = placesBlock({ checked: [
  { country: 'IN', name: 'India', mark: 'ok', yours: true, status: 'No matching recall', badge: { text: 'Checked by code, not guessed' } },
  { country: 'JP', name: 'Japan', mark: 'maybe', status: 'Unavailable' },
  { country: 'XX', name: 'Unknown', mark: 'skip', status: 'Not supported' },
] });
const detail = block.kids[1];
const dropdown = block.kids[2];
assert.equal(dropdown.tag, "details");
assert(!dropdown.open, "country cards are collapsed initially");
const rows = dropdown.kids[1].kids;
assert.equal(rows[0].className, 'country-chip ok your-country');
assert.equal(rows[1].className, 'country-chip maybe');
assert.equal(rows[0].kids[0].tag, 'img');
assert.equal(rows[0].kids[0].src, 'chrome-extension://test/assets/flags/in.png');
assert.equal(rows[2].kids[0].tag, 'span', 'unknown countries do not request a missing PNG');
assert.equal(detail.hidden, true, 'popup is hidden initially');
rows[0].onmouseenter();
assert.equal(detail.hidden, false);
assert.equal(rows[0].ariaExpanded, 'true');
assert(detail.text().includes('India (you)'));
rows[0].onmouseleave();
assert.equal(detail.hidden, true, 'popup closes when hover ends');
rows[1].onmouseenter();
assert.equal(rows[1].ariaExpanded, 'true');
assert(detail.text().includes('Unavailable'), 'other countries show their own actual status');
assert.equal(detail.className, 'country-detail maybe');
rows[1].onkeydown({ key: 'Escape' });
assert.equal(detail.hidden, true);
rows[2].onfocus();
assert(detail.text().includes('Not supported'), 'keyboard focus also shows country details');
rows[2].onblur();
assert.equal(detail.hidden, true);
assert(!block.text().includes('Checked by code'), 'country cards omit the repeated code badges');
for (const country of 'in jp au sg us kr tw id eu nz my th ph vn'.split(' ')) {
  const data = fs.readFileSync(path.join(EXT, 'assets/flags', country + '.png'));
  assert.equal(data.subarray(0, 8).toString('hex'), '89504e470d0a1a0a', country + ' is a real PNG');
}
const manifest = JSON.parse(read('manifest.json'));
assert(manifest.web_accessible_resources.some((r) => r.resources.includes('assets/flags/*.png')));
console.log('ok country flags: bundled PNGs, full-row home country, no repeated badges');
