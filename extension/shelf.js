const ICON = { unknown: 'Not checked yet', green: 'Looks fine so far', amber: 'Under review', red: 'Needs attention' };
const list = document.getElementById('list');
const empty = document.getElementById('empty');
const search = document.getElementById('shelf-search');
const filter = document.getElementById('shelf-filter');
const el = (tag, props = {}, ...kids) => { const n = Object.assign(document.createElement(tag), props); n.append(...kids); return n; };
const safeURL = value => { try { const url = new URL(value); return ['http:','https:'].includes(url.protocol) ? url.href : null; } catch { return null; } };
let products = [];
function render() {
  const now = Date.now();
  const weekAgo = now - 7 * 24 * 60 * 60 * 1000;
  const stats = {
    total: products.length,
    attention: products.filter(item => ['amber', 'red'].includes(item.level)).length,
    unchecked: products.filter(item => !['green', 'amber', 'red'].includes(item.level)).length,
    recent: products.filter(item => { const saved = Date.parse(item.saved_at); return saved >= weekAgo && saved <= now; }).length,
  };
  for (const [key, value] of Object.entries(stats)) document.getElementById(`stat-${key}`).textContent = value;
  document.getElementById('attention-ring').style.strokeDasharray = `${stats.total ? stats.attention / stats.total * 100 : 0} 100`;
  const levels = ['green', 'amber', 'red', 'unknown'];
  document.getElementById('status-distribution').replaceChildren(...levels.map(level => {
    const count = products.filter(item => (['green', 'amber', 'red'].includes(item.level) ? item.level : 'unknown') === level).length;
    const column = el('div', { className: `distribution-column ${level}`, title: `${ICON[level]}: ${count}` });
    const bar = el('span', { className: 'distribution-bar' });
    bar.style.height = `${stats.total ? count / stats.total * 42 : 0}px`;
    column.append(el('small', { textContent: count }), bar, el('small', { textContent: { green: 'FINE', amber: 'REVIEW', red: 'ALERT', unknown: 'NEW' }[level] }));
    return column;
  }));
  document.getElementById('pending-fill').style.width = `${stats.total ? stats.unchecked / stats.total * 100 : 0}%`;
  const days = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(now);
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() - (6 - index));
    const end = new Date(date);
    end.setDate(end.getDate() + 1);
    return { label: date.toLocaleDateString(undefined, { weekday: 'short' }), count: products.filter(item => {
      const saved = Date.parse(item.saved_at);
      return saved >= date.getTime() && saved < end.getTime() && saved <= now;
    }).length };
  });
  const maximum = Math.max(1, ...days.map(day => day.count));
  document.getElementById('shelf-activity').replaceChildren(...days.map(day => {
    const column = el('div', { className: 'activity-day', title: `${day.label}: ${day.count} saved` });
    const bar = el('span', { className: 'activity-bar' });
    bar.style.height = `${day.count / maximum * 44}px`;
    column.append(bar, el('small', { textContent: day.label.slice(0, 1) }));
    column.setAttribute('aria-label', `${day.label}: ${day.count} saved`);
    return column;
  }));
  const query = search.value.trim().toLowerCase();
  const visible = products.filter(item => `${item.title || ''} ${item.host || ''}`.toLowerCase().includes(query) && (filter.value === 'all' || (item.level || 'unknown') === filter.value));
  document.getElementById('shelf-count').textContent = products.length;
  empty.hidden = products.length > 0;
  document.getElementById('no-matches').hidden = !products.length || visible.length > 0;
  list.replaceChildren(...visible.map(item => {
    const level = Object.hasOwn(ICON,item.level) ? item.level : 'unknown';
    const url = safeURL(item.url);
    const imageURL = safeURL(item.image_url || item.image_urls?.[0]);
    const media = el(url ? 'a' : 'div', { className:'product-media', ...(url ? {href:url,target:'_blank',rel:'noopener'} : {}) });
    const fallback = el('div', {className:'product-placeholder'});
    fallback.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><circle cx="9" cy="10" r="1.6"/><path d="m4 17 4.6-4.4 3.4 3.1 3.1-2.6L20 17"/></svg><small>No image saved</small>';
    media.append(fallback);
    if(imageURL) {
      const image = el('img',{src:imageURL,alt:item.title || 'Saved product',loading:'lazy',referrerPolicy:'no-referrer'});
      image.addEventListener('error',()=>image.remove(),{once:true});
      media.append(image);
    }
    const title = el(url ? 'a' : 'span', {className:'product-title',textContent:item.title || 'Saved product',...(url?{href:url,target:'_blank',rel:'noopener'}:{})});
    const remove = el('button',{type:'button',className:'remove-product',textContent:'Remove'});
    remove.setAttribute('aria-label',`Remove ${item.title || 'product'} from My Shelf`);
    remove.addEventListener('click',async()=>{
      remove.disabled=true;
      const res=await chrome.runtime.sendMessage({type:'safeshelf:shelf-remove',id:item.id}).catch(()=>null);
      if(!res?.ok){remove.disabled=false;remove.textContent='Retry removal';} // on success the storage change redraws the list
    });
    const date = new Date(item.saved_at);
    const saved = Number.isNaN(date.getTime()) ? 'Saved on this device' : `Saved ${date.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'})}`;
    return el('li',{className:`product-card ${level}`},media,el('div',{className:'product-body'},el('div',{className:'product-source',textContent:item.host || 'Saved listing'}),title,el('span',{className:'status',textContent:ICON[level]}),el('div',{className:'product-footer'},el('span',{className:'meta',textContent:saved}),remove)));
  }));
}
async function load(){try { const {shelf=[]}=await chrome.storage.local.get('shelf');products=shelf;render(); } catch {empty.hidden=false;empty.textContent='Could not load your shelf. Reload to try again.';}}
search.addEventListener('input',render);
filter.addEventListener('change',render);
chrome.storage.onChanged.addListener((changes,area)=>{if(area==='local' && changes.shelf)load();});
load();
// Signed in, the shelf is also kept in the account and shown on the website; bring in changes made there.
async function sync(){
  const res=await chrome.runtime.sendMessage({type:'safeshelf:shelf-sync'}).catch(()=>null);
  const s=res?.ok?res.result:null;
  if(!s?.signedIn)return;
  const web=document.getElementById('shelf-web');
  web.href=s.website;web.hidden=false;
  document.getElementById('shelf-where').textContent=s.synced?'Saved to your account':'Saved on this device (account sync failed, retrying later)';
  document.getElementById('shelf-storage').textContent=s.synced?'Saved to your SafeShelf account, so it also shows on the website.':'Saved on this device; it goes to your account once the connection is back.';
}
sync();
addEventListener('focus',sync); // coming back from the website tab
