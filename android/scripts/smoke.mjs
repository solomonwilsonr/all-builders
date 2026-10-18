// Run with an installed debug app, adb on PATH, and a booted emulator/device.
// Exercises shared-text intake and the actual bundled client without spending AI quota.
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';
const adb = (...args) => execFileSync(process.env.ADB || 'adb', args, { encoding: 'utf8', timeout: 15000 }).trim();
const wait = ms => new Promise(r => setTimeout(r, ms));
const link = 'https://www.amazon.in/dp/B0CFFBZ23F';
adb('shell','am','start','-n','org.safeshelf.android/.MainActivity','-a','android.intent.action.SEND','-t','text/plain','--es','android.intent.extra.TEXT',link);
let pid, pages;
for (let i=0;i<40;i++) {
  try {
    pid=adb('shell','pidof','org.safeshelf.android');
    adb('forward','tcp:9223',`localabstract:webview_devtools_remote_${pid}`);
    pages=await (await fetch('http://127.0.0.1:9223/json', {signal: AbortSignal.timeout(5000)})).json();
    if(pages[0]?.webSocketDebuggerUrl) break;
  } catch {}
  await wait(1000);
}
assert.ok(pages?.[0]?.webSocketDebuggerUrl, 'WebView debugging endpoint');
const ws = new WebSocket(pages[0].webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
let id=0; const replies=new Map();
ws.onmessage = event => { const msg=JSON.parse(event.data); if(replies.has(msg.id)){replies.get(msg.id)(msg);replies.delete(msg.id);} };
const evaluate = async expression => {
  const request=++id;
  const result=new Promise(resolve=>replies.set(request,resolve));
  ws.send(JSON.stringify({id:request,method:'Runtime.evaluate',params:{expression,returnByValue:true}}));
  const response=await result;
  assert.ok(!response.result.exceptionDetails, JSON.stringify(response.result.exceptionDetails));
  return response.result.result.value;
};
try {
  let ready=false;
  for(let i=0;i<40;i++){
    ready=await evaluate(`typeof window.safeshelfSignIn==='function' && document.getElementById('q')?.value===${JSON.stringify(link)}`);
    if(ready)break; await wait(1000);
  }
  assert.ok(ready,'shared link is prefilled after Firebase client initializes');
  assert.equal(await evaluate("getComputedStyle(document.documentElement).getPropertyValue('--blue').trim()"),'#0271e4','website blue token');
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.qbox')).borderRadius"),'28px','reference-style rounded composer');
  assert.ok(await evaluate("document.fonts.check('14px \"Schibsted Grotesk\"')"),'bundled website font');
  assert.equal(await evaluate("document.querySelectorAll('#log .row.user').length"),0,'no automatic submission');
  assert.equal(await evaluate("document.getElementById('product').value"),'unmatched','shopper checks do not default to a demo product');
  assert.equal(await evaluate("getComputedStyle(document.getElementById('toolsBtn')).display"),'none','developer controls hidden');
  await evaluate("document.getElementById('clear').click();true");
  assert.ok(await evaluate("document.getElementById('ux-confirm').open"),'new check asks before discarding draft');
  assert.equal(await evaluate("window.androidUx.back()"),'stay','Back dismisses confirmation before navigating');
  assert.equal(await evaluate("document.getElementById('q').value"),link,'Back keeps the draft');
  await evaluate("document.getElementById('send').disabled=true;true");
  assert.ok(await evaluate("document.getElementById('clear').disabled && document.getElementById('scan').disabled"),'busy check cannot be cleared or replaced');
  await evaluate("document.getElementById('send').disabled=false;true");
  await evaluate("window.safeshelfSignIn();true");
  assert.ok(await evaluate("!!document.querySelector('.ssa-modal input[type=password]')"),'email sign-in UI');
  assert.ok(await evaluate("document.querySelector('.ssa-modal .ssa').getBoundingClientRect().top >= 0"),'tall sign-in card starts inside the viewport');
  assert.ok(await evaluate("document.querySelector('.ssa-close').getBoundingClientRect().top >= 0"),'sign-in close button stays reachable');
  assert.ok(await evaluate("[...document.querySelectorAll('.ssa-modal button')].filter(x=>x.textContent.includes('Google')).every(x=>x.hidden)"),'Google OAuth hidden in embedded client');
  await evaluate("document.querySelector('.ssa-modal').click();document.getElementById('shelfBtn').click();true");
  assert.equal(await evaluate("document.getElementById('shelf').hidden"),false,'watchlist drawer opens');
  assert.equal(await evaluate("getComputedStyle(document.querySelector('#shelf .p')).position"),'static','shelf description stays in document flow');
  assert.ok(await evaluate("document.querySelector('#shelf .p').getBoundingClientRect().bottom <= document.getElementById('shelfList').getBoundingClientRect().top"),'shelf description does not overlap products');
  await evaluate("document.getElementById('shelfClose').click();true");
  assert.equal(await evaluate("document.getElementById('shelf').hidden"),true,'watchlist drawer closes');
  await evaluate("document.getElementById('clear').click();document.querySelector('#ux-confirm .btn-blue').click();true");
  assert.equal(await evaluate("document.getElementById('q').value"),'','confirmed new check clears the draft');
  assert.equal(await evaluate("document.getElementById('product').value"),'unmatched','new checks use the shopper product context');
  console.log('PASS: bundled chat, Firebase UI initialization, shared-link review, no automatic submission, email sign-in form, Google restriction, shelf open/close, real-product defaults, draft confirmation, Back behavior and busy guards.');
} finally { ws.close(); adb('forward','--remove','tcp:9223'); }
