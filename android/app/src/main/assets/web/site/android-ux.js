/* Shopper-focused Android behavior; the website and its API logic remain untouched. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const q = $('q'), product = $('product'), composer = document.querySelector('.composer');
  if (!q || !product || !composer) return;
  const make = (tag, text, props = {}) => Object.assign(document.createElement(tag), {textContent:text,...props});
  const status = make('p','Paste a link or scan a label to get started.',{id:'ux-status'});
  status.setAttribute('role','status'); status.setAttribute('aria-live','polite'); composer.prepend(status);
  const announce = text => { status.textContent = text; };
  const readDraft = () => { try { return sessionStorage.getItem('ss-android-draft') || ''; } catch { return ''; } };
  const saveDraft = () => { try { sessionStorage.setItem('ss-android-draft',q.value); } catch {} };
  if (!q.value) { q.value=readDraft(); q.dispatchEvent(new Event('input')); }
  q.addEventListener('input',saveDraft);
  $('ask').addEventListener('submit',() => setTimeout(saveDraft,0));

  // A real shopper should never start a check against a preselected demo charger.
  product.value='unmatched'; product.onchange?.();
  q.placeholder='Paste a product link or ask a question…';
  const context=make('span','Your product',{id:'ux-context'}); document.querySelector('.chat-bar').prepend(context);
  const updateContext=()=>{
    const linked=$('linked');
    context.textContent = !linked.hidden ? (linked.querySelector('b')?.textContent || 'Your product') : product.value==='unmatched' ? 'Your product' : 'Sample: Kelvo CX-65 charger';
    context.title=context.textContent;
  };
  new MutationObserver(updateContext).observe($('about'),{subtree:true,childList:true,attributes:true});
  product.addEventListener('change',updateContext);
  const button=(label,action)=>{const b=make('button',label,{type:'button',className:'starter'});b.onclick=action;return b;};
  const paste=button('Paste a product link',()=>{q.focus();announce('Touch and hold the message box to paste your shopping link.');});
  const scan=button('Scan a product label',()=>$('scan').click());
  const sample=button('Try a sample — no product needed',()=>{
    product.value='SS-P-10291'; product.onchange?.(); updateContext();
    q.value='Is this Kelvo CX-65 charger safe?'; q.dispatchEvent(new Event('input')); q.focus();
    announce('Sample selected. Press Send to use a check, or start a new check for your own product.');
  });
  sample.classList.add('ux-sample'); $('starters').replaceChildren(paste,scan,sample);
  document.querySelector('.hello .lead').textContent='Get a clear answer with sources. Start with a shopping link or a photo of the model label.';
  $('clear').setAttribute('aria-label','Start a new product check');
  $('clear').title='New product check';
  $('send').setAttribute('aria-label','Send for a product check');
  const sendText=$('send').querySelector('span'); if(sendText)sendText.textContent='Send';
  $('attach').setAttribute('aria-label','Attach a product photo, screenshot or PDF manual');
  q.setAttribute('enterkeyhint','enter');
  q.setAttribute('aria-describedby','ux-status checksLeft');
  $('checksLeft').setAttribute('role','status');

  const dialog=document.createElement('dialog'); dialog.id='ux-confirm';
  const heading=make('h2','Start a new check?'); heading.id='ux-confirm-title';
  dialog.setAttribute('aria-labelledby',heading.id);
  dialog.append(heading,make('p','This clears the current conversation and attachments. Products saved to My Shelf stay saved.'));
  const controls=make('div','',{className:'ux-dialog-actions'});
  const cancel=make('button','Keep this chat',{type:'button',className:'btn btn-ghost'});
  const confirm=make('button','Start new check',{type:'button',className:'btn btn-blue'});
  cancel.onclick=()=>dialog.close(); controls.append(cancel,confirm);dialog.append(controls);document.body.append(dialog);
  const clear=$('clear').onclick;
  const reset=()=>{
    product.value='unmatched';clear();q.value='';saveDraft();updateContext();
    announce('New check ready. Paste a shopping link or scan a product label.');
  };
  confirm.onclick=()=>{dialog.close();reset();};
  $('clear').onclick=()=>{
    if($('send').disabled)return;
    if(q.value.trim() || !$('attached').hidden || document.querySelector('#log .row')){dialog.showModal();cancel.focus();}
    else reset();
  };
  $('shelfClose').addEventListener('click',event=>{if(event.isTrusted) location.href='safeshelf://check';});
  // Shopper-friendly shelf guidance and a useful empty state.
  document.querySelector('#shelf .p').textContent='Products you choose to watch appear here. Open a product check and tap “Watch for recalls” to add one. Open this shelf for the latest status; phone notifications are not enabled yet.';
  const shelfObserver=new MutationObserver(()=>{
    const li=$('shelfList').firstElementChild;
    if(li && !li.querySelector('button') && /Nothing saved yet/.test(li.textContent)){
      li.replaceChildren(make('strong','Your shelf is ready for its first product'),make('p','Check a product, then choose “Watch for recalls” beneath the answer.'));
      const start=make('button','Check a product',{type:'button',className:'btn btn-blue'});
      start.onclick=()=>{$('shelfClose').click();location.href='safeshelf://check';q.focus();};li.append(start);
    }
  });
  shelfObserver.observe($('shelfList'),{childList:true,subtree:true});

  const syncBusy=()=>{
    const busy=$('send').disabled;
    document.querySelector('.chat').setAttribute('aria-busy',String(busy));
    [$('clear'),$('scan'),$('attach'),...$('starters').querySelectorAll('button')].forEach(b=>b.disabled=busy);
    if(sendText)sendText.textContent=busy?'Wait…':'Send';
    if(busy)announce('Checking your product… This can take a minute. Keep the app open; you can visit My Shelf while you wait.');
    else announce(navigator.onLine ? 'Review the sources and ask a follow-up, or start a new product check.' : 'You’re offline. Your draft is kept. Reconnect before sending.');
  };
  new MutationObserver(syncBusy).observe($('send'),{attributes:true,attributeFilter:['disabled']});
  addEventListener('offline',()=>announce('You’re offline. Your draft is kept. Reconnect before sending.'));
  addEventListener('online',()=>announce('Connection restored. Press Send when you are ready.'));
  window.androidUx={announce,back(){
    if(dialog.open){dialog.close();return 'stay';}
    const modal=document.querySelector('.ssa-modal');if(modal){modal.click();return 'stay';}
    if(!$('tools').hidden){$('toolsClose').click();return 'stay';}
    if(!$('shelf').hidden){$('shelfClose').click();return 'shelf';}
    return 'home';
  }};
})();
