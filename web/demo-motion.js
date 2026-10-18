// Decorative motion stays independent of the live demo's data and controls.
(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const fine = matchMedia('(hover: hover) and (pointer: fine)');
  const effects = new Set();
  const play = (el, frames, options) => {
    if (reduced.matches) return;
    const animation = el.animate(frames, options);
    effects.add(animation);
    animation.finished.catch(() => {}).finally(() => effects.delete(animation));
    return animation;
  };
  const halo = document.createElement('div');
  halo.className = 'demo-cursor';
  const layer = document.createElement('div');
  layer.className = 'demo-click-layer';
  const progress = document.createElement('div');
  progress.className = 'demo-progress';
  [halo, layer, progress].forEach(el => el.setAttribute('aria-hidden', 'true'));
  document.body.append(halo, layer, progress);

  const targets = '.top .logo, .top .links, .nav-end, .dhero-in > *, .journey-head, .journey ol > li, .block-head > *, .role-block, .split > div, .how3 > div, .rules > *, .cta > :not(img), .foot .cols > div';
  const reveal = new IntersectionObserver(entries => {
    let stagger = 0;
    entries.forEach(({ target, isIntersecting }) => {
      if (!isIntersecting || target.getBoundingClientRect().height === 0) return;
      reveal.unobserve(target);
      play(target, [{ opacity: 0, translate: '0 20px' }, { opacity: 1, translate: '0 0' }], {
        duration: 650, delay: Math.min(stagger++ * 65, 300), easing: 'cubic-bezier(.22,1,.36,1)', fill: 'backwards',
      });
    });
  }, { threshold: .08 });
  document.querySelectorAll(targets).forEach(el => reveal.observe(el));

  const cards = [...document.querySelectorAll('.dstats li, .journey ol > li, .split > div, .how3 > div')];
  cards.forEach(el => el.classList.add('demo-motion-card'));
  const hero = document.querySelector('.dhero');
  let frame = 0, x = 0, y = 0, active = null;
  const resetCard = () => {
    if (!active) return;
    ['--tilt-x', '--tilt-y', '--light-x', '--light-y'].forEach(key => active.style.removeProperty(key));
    active.classList.remove('is-pointer');
    active = null;
  };
  const clear = () => {
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
    halo.classList.remove('is-visible');
    resetCard();
    hero?.style.removeProperty('--drift-x');
    hero?.style.removeProperty('--drift-y');
  };
  document.addEventListener('pointermove', event => {
    if (reduced.matches || !fine.matches || event.pointerType !== 'mouse') return;
    x = event.clientX; y = event.clientY;
    const card = event.target.closest('.demo-motion-card');
    if (card !== active) { resetCard(); active = card; }
    halo.classList.add('is-visible');
    halo.classList.toggle('is-action', !!event.target.closest('a, button, input, textarea, select, summary'));
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      halo.style.left = `${x}px`; halo.style.top = `${y}px`;
      if (active) {
        const box = active.getBoundingClientRect();
        const px = Math.max(0, Math.min(1, (x - box.left) / box.width));
        const py = Math.max(0, Math.min(1, (y - box.top) / box.height));
        active.style.setProperty('--tilt-x', `${(0.5 - py) * 4}deg`);
        active.style.setProperty('--tilt-y', `${(px - 0.5) * 4}deg`);
        active.style.setProperty('--light-x', `${px * 100}%`);
        active.style.setProperty('--light-y', `${py * 100}%`);
        active.classList.add('is-pointer');
      }
      if (hero) {
        const box = hero.getBoundingClientRect();
        const inside = y >= box.top && y <= box.bottom;
        hero.style.setProperty('--drift-x', inside ? `${(x / innerWidth - .5) * 18}px` : '0px');
        hero.style.setProperty('--drift-y', inside ? `${((y - box.top) / box.height - .5) * 14}px` : '0px');
      }
    });
  }, { passive: true });
  document.addEventListener('pointerleave', clear);
  window.addEventListener('blur', clear);
  document.addEventListener('click', event => {
    if (reduced.matches || !fine.matches || event.detail === 0) return;
    while (layer.childElementCount >= 4) layer.firstElementChild.remove();
    const burst = document.createElement('span');
    burst.className = 'demo-burst';
    burst.style.left = `${event.clientX}px`; burst.style.top = `${event.clientY}px`;
    layer.append(burst);
    const ring = document.createElement('i');
    ring.className = 'demo-ring'; burst.append(ring);
    const animation = play(ring, [{ transform: 'scale(.25)', opacity: .8 }, { transform: 'scale(1.7)', opacity: 0 }], { duration: 620, easing: 'ease-out' });
    for (let i = 0; i < 6; i++) {
      const spark = document.createElement('i'); spark.className = 'demo-spark'; burst.append(spark);
      const angle = i * Math.PI / 3;
      play(spark, [{ transform: 'translate(0,0) scale(1)', opacity: .9 }, { transform: `translate(${Math.cos(angle) * 32}px,${Math.sin(angle) * 32}px) scale(0)`, opacity: 0 }], { duration: 480, easing: 'ease-out' });
    }
    animation.finished.catch(() => {}).finally(() => burst.remove());
    const control = event.target.closest('button:not(:disabled), .jbtn');
    if (control) play(control, [{ scale: '1' }, { scale: '.96', offset: .3 }, { scale: '1' }], { duration: 260, easing: 'ease-out' });
  });
  const scroll = () => {
    clear();
    const range = document.documentElement.scrollHeight - innerHeight;
    progress.style.transform = `scaleX(${range > 0 ? Math.min(1, Math.max(0, scrollY / range)) : 0})`;
  };
  addEventListener('scroll', scroll, { passive: true });
  addEventListener('resize', scroll, { passive: true });
  new ResizeObserver(scroll).observe(document.body);
  scroll();
  reduced.addEventListener('change', () => {
    clear();
    if (reduced.matches) { effects.forEach(animation => animation.cancel()); layer.replaceChildren(); }
  });
  fine.addEventListener('change', clear);
  document.addEventListener('visibilitychange', () => { if (document.hidden) clear(); });
})();
