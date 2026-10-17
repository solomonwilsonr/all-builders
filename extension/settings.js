import { API_BASE, SHELF_SYNC } from './config.js';
// Settings that take one of a few values. The first value is the default. Theme ones are applied by appearance.js (pages) and content.js (widget).
const CHOICES = {
 gradient: [['off','Off'],['on','On']],
 appearance: [['light','Light'],['dark','Dark'],['system','System']],
 accent: [['blue','Blue'],['lime','Lime'],['mint','Mint'],['sky','Sky'],['lilac','Lilac'],['peach','Peach'],['sand','Sand']],
 font: [['geist','Geist'],['system','System'],['rounded','Rounded'],['serif','Serif']],
 icons: [['regular','Regular'],['light','Light'],['bold','Bold']],
 widgetSide: [['right','Right'],['left','Left']],
 widgetSize: [['regular','Regular'],['compact','Compact']],
 widgetSurface: [['glass','Glass'],['solid','Solid']],
 widgetChat: [['popup','Pop-up'],['drawer','Drawer']],
};
CHOICES.appearance.default = 'system';
const first = key => CHOICES[key].default || CHOICES[key][0][0];
const valid = (key,value) => CHOICES[key].some(([v])=>v===value) ? value : first(key);
const defaults = { enabled: true, costGuard: true, ...Object.fromEntries(Object.keys(CHOICES).map(k=>[k,first(k)])) };
let saved = {...defaults}, state = {...defaults}, active = 'general';
let usage = {total:0,calls:0}, counts = {shelf:0,chatHistory:0};
const panel = document.querySelector('#panel');
const esc = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const head = (title,text) => `<header class="set-head"><h2>${title}</h2><p>${text}</p></header>`;
const group = (title,text,rows) => `<section class="set-group"><div class="set-group-text"><h3>${title}</h3><p>${text}</p></div><div class="set-rows">${rows}</div></section>`;
const row = (title,detail,control) => `<div class="set-row"><div class="set-row-text"><span class="set-row-title">${title}</span><span class="set-row-detail">${detail}</span></div>${control}</div>`;
const toggle = (key,label) => `<input class="set-switch" type="checkbox" role="switch" data-field="${key}" aria-label="${label}" ${state[key]?'checked':''}>`;
const figures = items => `<div class="set-figures">${items.map(([value,label,extra=''])=>`<div class="set-figure"><strong>${value}</strong><span>${label}</span>${extra}</div>`).join('')}</div>`;
// A segmented control for one CHOICES key. Font buttons are set in their own typeface.
const choice = (key,label) => `<div class="set-choice" role="group" aria-label="${label}">${CHOICES[key].map(([value,name])=>`<button type="button" data-choice="${key}" data-value="${value}" aria-pressed="${state[key]===value}"${key==='font'?` data-font="${value}"`:''}>${name}</button>`).join('')}</div>`;
const swatches = () => `<div class="set-swatches" role="group" aria-label="Accent color">${CHOICES.accent.map(([value,name])=>`<button type="button" class="set-swatch" data-choice="accent" data-value="${value}" data-accent="${value}" aria-pressed="${state.accent===value}" aria-label="${name}" title="${name}"><span></span></button>`).join('')}</div>`;
const nameOf = key => CHOICES[key].find(([v])=>v===state[key])[1];
// The same paths as the widget's side rail (content.js), so the preview shows the real buttons.
const RAIL = { ask:'M4 5h16v11H9l-5 4z', save:'M7 3h10a1 1 0 011 1v17l-6-4-6 4V4a1 1 0 011-1z', shelf:'M4 4h16a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1z M5 9v10a1 1 0 001 1h12a1 1 0 001-1V9 M10 13h4', check:'M12 3l7 3v5c0 5-3.2 8.2-7 10-3.8-1.8-7-5-7-10V6z M9 12l2 2 4-4' };
const railIcon = kind => `<span class="lp-btn ${kind==='save'?'on':''}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${RAIL[kind]}"/></svg><small>${({ask:"Ask",save:"Save",shelf:"Shelf",check:"Check"})[kind]}</small></span>`;
const preview = () => `<div class="look-preview" aria-label="Preview of your theme" role="img" data-gradient="${state.gradient}" data-accent="${state.accent}" data-font="${state.font}" data-icons="${state.icons}" data-side="${state.widgetSide}" data-size="${state.widgetSize}" data-surface="${state.widgetSurface}" data-chat="${state.widgetChat}">
 <div class="lp-page"><strong>Saved products</strong><span>Electric heated throw blanket</span><em>Under review</em></div>
 <div class="lp-chat"><i></i><i></i><i></i><b></b></div>
 <div class="lp-rail">${['ask','save','shelf','check'].map(railIcon).join('')}</div></div>`;
const isAdmin = () => document.documentElement.dataset.role === 'admin';
document.addEventListener('safeshelf:role', () => render());
function render(){
 if(active==='admin' && !isAdmin()) active='general';
 panel.toggleAttribute('data-admin-only', active==='admin');
 document.querySelectorAll('[data-tab]').forEach(b=>{const selected=b.dataset.tab===active;b.setAttribute('aria-selected',selected);b.tabIndex=selected?0:-1;});
 panel.setAttribute('aria-labelledby',`tab-${active}`);
 if(active==='general') panel.innerHTML=head('How SafeShelf works as you shop','Turn the in-page button on or off.')
  +group('Product checks','The SafeShelf button on supported shopping pages.',row('Enable SafeShelf','Show the in-page button on supported product pages.',toggle('enabled','Enable SafeShelf'))+`<p class="set-note">SafeShelf only sends a product’s details for a check when you ask for one.</p>`);
 if(active==='theme') panel.innerHTML=head('Make SafeShelf yours','Color, type and icons for SafeShelf’s pages, and how the widget looks on shopping sites. Changes apply as soon as you pick them.')
  +'<div class="theme-layout"><aside class="theme-preview" aria-label="Live theme preview"><h3>Preview</h3>'+preview()+'<p>Updates as you change your settings.</p></aside><div class="theme-controls">'
  +group('Mode','Light, dark, or follow your device.',row('Color mode','For every SafeShelf page.',choice('appearance','Color mode')))
  +group('Gradient effect','Optional color gradients across SafeShelf pages.',row('Gradient effect','Off uses a flat background. Changes apply immediately.',choice('gradient','Gradient effect')))
  +group('Accent color','Highlights, the wash at the top of each page, and the saved bookmark.',row('Accent',nameOf('accent'),swatches()))
  +group('Type and icons','The typeface for SafeShelf’s pages, and the line weight of every icon.',row('Font',`${nameOf('font')}. The widget uses it when your computer has it.`,choice('font','Font'))+row('Icons',`${nameOf('icons')} line weight.`,choice('icons','Icon weight')))
  +group('Widget on shopping pages','The SafeShelf buttons beside a product.',row('Side','Which edge of the window it sits on. You can also drag the handle above the buttons.',choice('widgetSide','Widget side'))+row('Size','Compact takes less room on small screens.',choice('widgetSize','Widget size'))+row('Look','Glass lets the shop show through.',choice('widgetSurface','Widget look'))+row('Panels open in','The safety check and chat: a pop-up beside the buttons, or a drawer docked to the edge of the window.',choice('widgetChat','Panels open in')))+' </div></div>';
 if(active==='usage') panel.innerHTML=head('What your AI checks have cost','A running estimate kept in this browser. It is not a bill.')
  +figures([[`₹${Number(usage.total||0).toFixed(2)}`,'Estimated AI spend since your last reset'],[Number(usage.calls||0),'AI requests counted by the extension']])
  +group('Usage counter','Starts the estimate again from zero. Your billing does not change.',row('Reset usage counter','Clears the local estimate only.','<button class="set-button" type="button" data-action="reset-spend">Reset counter</button>'));
 if(active==='data') panel.innerHTML=head('What stays in this browser','Saved products and chat history are kept in this Chrome profile.')
  +figures([[counts.shelf,'Saved products','<a class="set-link" href="shelf.html">Open My Shelf</a>'],[counts.chatHistory,'Chat history entries']])
  +group('Sync','Where your saved products go.',row('Shelf API sync','Whether saved products are also sent to the Shelf API.',`<span class="set-value">${SHELF_SYNC?'On':'Off, browser storage only'}</span>`));
 if(active==='about') panel.innerHTML=head('About SafeShelf','SafeShelf checks product safety and how far a listing can be trusted.')
  +group('Extension details','The installed copy and the service it checks against.',row('Version','Installed extension version.',`<span class="set-value">${esc(chrome.runtime.getManifest().version)}</span>`));
 if(active==='admin' && isAdmin()) {
  panel.innerHTML=head('Administration','Administrator diagnostics and developer tools.')
   +group('Paid requests','Control confirmation before AI spending.',row('Ask before paid requests','Confirm the estimated AI cost before a paid request starts.',toggle('costGuard','Ask before paid requests')))
   +group('Developer tools','API availability and investigation details.',row('API endpoint','Service used by this extension.',`<span class="set-value">${esc(API_BASE)}</span>`)+row('Judges’ Lab','Catalog scans, benchmarks and investigation diagnostics.','<a class="set-button" href="lab.html">Open the Lab</a>'))
   +group('API status','Verified by the backend.', '<p id="admin-status-output" role="status">Loading…</p><button class="set-button" id="admin-status-refresh">Refresh status</button>');
  const refresh = async () => {
   const output=panel.querySelector('#admin-status-output');
   output.textContent='Loading…';
   try {
    const reply=await chrome.runtime.sendMessage({type:'safeshelf:admin-status'});
    if(!reply?.ok) throw new Error(reply?.error || 'Access denied');
    output.textContent=`Online · ${reply.result.mock?'Mock':'Live'} · ${reply.result.real_endpoints.length} live endpoints`;
   } catch(error) { output.textContent=error.message; }
  };
  panel.querySelector('#admin-status-refresh').onclick=refresh;
  refresh();
 }

}
function dirty(){document.querySelector('#save-note').textContent='Changes save automatically';}
function toast(message){document.querySelector('#save-note').textContent=message;}
const fromStore = data => ({enabled:data.enabled!==false,costGuard:data.costGuard!==false,...Object.fromEntries(Object.keys(CHOICES).map(k=>[k,valid(k,data[k])]))});
async function load(){try{const data=await chrome.storage.local.get(['enabled','costGuard',...Object.keys(CHOICES),'spend','shelf','chatHistory']);saved=fromStore(data);state={...saved};usage=data.spend||{total:0,calls:0};counts={shelf:(data.shelf||[]).length,chatHistory:(data.chatHistory||[]).length};render();dirty();}catch{toast('Could not load extension settings. Reload to try again.');}}
document.querySelectorAll('[data-tab]').forEach(b=>{b.addEventListener('click',()=>{active=b.dataset.tab;render();});b.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const tabs=[...document.querySelectorAll('[data-tab]')].filter(t=>!t.hasAttribute('data-admin-only')||isAdmin()),i=tabs.indexOf(b);tabs[e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length].click();document.querySelector('[aria-selected="true"]').focus();});});
// Theme choices are cosmetic and previewed, so they save the moment you pick them: open SafeShelf pages and shopping tabs update right away.
panel.addEventListener('click',async e=>{const button=e.target.closest('[data-choice]');if(!button)return;const key=button.dataset.choice,value=valid(key,button.dataset.value);state[key]=value;render();panel.querySelector(`[data-choice="${key}"][data-value="${value}"]`)?.focus();try{await chrome.storage.local.set({[key]:value});saved[key]=value;}catch{toast('Could not save that choice. Please try again.');}dirty();});
panel.addEventListener('change',async e=>{const key=e.target.dataset.field;if(!key)return;const previous=state[key];state[key]=e.target.checked;try{if(key==='costGuard'){const reply=await chrome.runtime.sendMessage({type:'safeshelf:set-cost-guard',enabled:state[key]});if(!reply?.ok)throw new Error(reply?.error||'Access denied');}else{await chrome.storage.local.set({[key]:state[key]});}saved[key]=state[key];dirty();}catch{state[key]=previous;render();toast('Could not save that setting. Please try again.');}});
panel.addEventListener('click',async e=>{if(!e.target.closest('[data-action="reset-spend"]'))return;try{await chrome.storage.local.set({spend:{total:0,calls:0}});usage={total:0,calls:0};render();toast('Local usage counter reset.');}catch{toast('Could not reset the usage counter.');}});
document.querySelector('#reset').addEventListener('click',async()=>{try{const {costGuard,...personalDefaults}=defaults;await chrome.storage.local.set(personalDefaults);saved={...personalDefaults,costGuard:saved.costGuard};state={...saved};render();toast('Default settings restored.');}catch{toast('Could not restore defaults. Please try again.');}});
chrome.storage.onChanged.addListener((changes,area)=>{if(area!=='local')return;const fresh=fromStore(Object.fromEntries(Object.entries(changes).map(([k,c])=>[k,c.newValue])));for(const key of Object.keys(defaults)){if(changes[key]){const edited=state[key]!==saved[key];saved[key]=fresh[key];if(!edited)state[key]=saved[key];}}if(changes.spend)usage=changes.spend.newValue||{total:0,calls:0};for(const key of ['shelf','chatHistory'])if(changes[key])counts[key]=(changes[key].newValue||[]).length;render();dirty();});
load();
