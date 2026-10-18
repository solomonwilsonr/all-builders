/* Real Android screenshots, with keyboard-accessible screen navigation. */
(() => {
  const screens = {
    home: {number:'01 / 04', title:'Start with what you have.', copy:'Paste a shopping link or type a question. Prefer a photo or your voice? The shortcuts are right there. Your question opens in Check for you to review before sending.', points:['A product-link and question field','Label scans and voice input from Home','Quick access to My Shelf and Eddy'], caption:'Home · Your next check starts here.', alt:'SafeShelf Home screen with the product question field and shortcuts'},
    chat: {number:'02 / 04', title:'Ask Eddy. Keep asking.', copy:'Bring a product link, a label photo or a question. Eddy explains what the available evidence says. Open the sources, ask a follow-up, or start a fresh product check.', points:['Links, photos and PDF manual attachments','A visible Send button and answer-language selection','Your draft stays put; starting over asks first'], caption:'Check · A conversation, with evidence.', alt:'SafeShelf Check screen showing Eddy, the product question box, language selector and Send button'},
    shelf: {number:'03 / 04', title:'Keep your products close.', copy:'When an answer supports it, choose “Watch for recalls”. Come back to My Shelf to see your watched products and their latest status from the service.', points:['One place for the products you choose to watch','A helpful starting point when your shelf is empty','Status in the app; background push alerts are not connected yet'], caption:'My Shelf · Your watched products, together.', alt:'SafeShelf My Shelf screen with guidance to check a product and save it for recall watching'},
    account: {number:'04 / 04', title:'Your SafeShelf. Your choice.', copy:'Sign in with email, create an account, or try guest access. Account keeps sign-in information and check availability close, alongside clear guidance about saved products and privacy.', points:['Email and guest sign-in inside the app','Your account and remaining checks when available','Clear information about privacy and current limits'], caption:'Account · A little more peace of mind.', alt:'SafeShelf Account screen showing sign-in, product-watch and privacy information'}
  };
  const tabs = [...document.querySelectorAll('[data-screen]')];
  const get = id => document.getElementById(id);
  function show(tab, focus = false) {
    const key = tab.dataset.screen, screen = screens[key];
    if (!screen) return;
    tabs.forEach(button => {const active = button === tab;button.setAttribute('aria-selected',String(active));button.tabIndex = active ? 0 : -1;});
    get('screen-panel').setAttribute('aria-labelledby',tab.id);
    get('screen-number').textContent = screen.number;
    get('screen-title').textContent = screen.title;
    get('screen-copy').textContent = screen.copy;
    get('screen-points').replaceChildren(...screen.points.map(text => {const item = document.createElement('li');item.textContent = text;return item;}));
    get('screen-caption').textContent = screen.caption;
    get('screen-image').src = `assets/app/${key}.webp`;get('screen-image').alt = screen.alt;
    get('screen-full').href = `assets/app/${key}.webp`;
    if (focus) tab.focus();
  }
  tabs.forEach((tab,index) => {
    tab.addEventListener('click',() => show(tab));
    tab.addEventListener('keydown',event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) {event.preventDefault();show(tabs[next],true);}
    });
  });
})();
