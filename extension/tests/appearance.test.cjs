const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
let dark = false, storageListener, mediaListener;
const doc = { dataset: {} }, host = { setAttribute(k,v) { this[k]=v; } };
const context = {
 location: { protocol:'chrome-extension:' }, document: {documentElement:doc},
 matchMedia: () => ({get matches(){return dark;},addEventListener(_,fn){mediaListener=fn;},removeEventListener(){}}),
 chrome:{ storage:{local:{get(_,cb){cb({appearance:'system'});}},onChanged:{addListener(fn){storageListener=fn;},removeListener(){}}}}
};
vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../appearance.js'),'utf8'),context);
assert.equal(doc.dataset.theme,'light');
context.SafeShelfAppearance.register(host);
dark=true;mediaListener();
assert.equal(doc.dataset.theme,'dark');assert.equal(host['data-theme'],'dark');
storageListener({appearance:{newValue:'light'}},'local');
assert.equal(doc.dataset.theme,'light');assert.equal(host['data-theme'],'light');
mediaListener();assert.equal(doc.dataset.theme,'light');
storageListener({appearance:{newValue:'dark'}},'local');assert.equal(doc.dataset.theme,'dark');
storageListener({appearance:{newValue:'invalid'}},'local');dark=false;mediaListener();assert.equal(doc.dataset.theme,'light');
console.log('ok appearance: saved choices, system changes and shadow hosts');
assert.equal(doc.dataset.gradient,'off');
storageListener({gradient:{newValue:'on'}},'local');
assert.equal(doc.dataset.gradient,'on');assert.equal(host['data-gradient'],'on');
storageListener({gradient:{newValue:'invalid'}},'local');
assert.equal(doc.dataset.gradient,'off');
