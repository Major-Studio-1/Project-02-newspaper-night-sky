/* Newspaper Night Sky: the glass controls shared by the Telescope and Pulses pages. Copied next to the pages by
   work/build_pulse_explorer.py; the styles are in site.css.
   A single choice (.seg.slide) gets a glass thumb that slides to the chosen option, the button with aria-pressed="true".
   Tap an option, drag the thumb along the group (it settles on the nearest open option when let go), or use the arrow
   keys (Home and End go to the ends). Options with aria-disabled="true" are skipped. A page sets aria-pressed itself,
   then calls Glass.sync(). A group with data-roving is one stop for the Tab key (for long groups such as the years).
   While the thumb is dragged, the group sends "glass:near" events naming the option under it. */
window.Glass = (() => {
  const segs = [], thumbs = new Map(), at = new Map();
  let swallowClick = false;
  const open = seg => [...seg.querySelectorAll('button')].filter(b => b.getAttribute('aria-disabled') !== 'true');
  function sync(force) {
    for (const seg of segs) {
      if (seg.classList.contains('dragging')) continue;
      const t = thumbs.get(seg), b = seg.querySelector('button[aria-pressed="true"]');
      if ('roving' in seg.dataset) {   // one Tab stop: the chosen option (or the first)
        const first = b || seg.querySelector('button');
        for (const x of seg.querySelectorAll('button')) x.tabIndex = x === first ? 0 : -1;
      }
      if (!force && at.get(seg) === b) continue;
      if (!b) { t.style.opacity = '0'; at.set(seg, b); continue; }
      if (!b.offsetWidth) continue;   // not laid out yet (hidden); the resize observer catches it later
      at.set(seg, b); t.style.opacity = '1'; t.style.width = b.offsetWidth + 'px'; t.style.transform = `translateX(${b.offsetLeft}px)`;
      if (!seg.classList.contains('ready')) requestAnimationFrame(() => requestAnimationFrame(() => seg.classList.add('ready')));   // no slide in from nowhere at first
    }
  }
  function enhance(seg) {
    const thumb = document.createElement('i'); thumb.className = 'thumb'; thumb.setAttribute('aria-hidden', 'true'); seg.prepend(thumb); thumbs.set(seg, thumb);
    const thumbX = (d, dx) => Math.max(2, Math.min(seg.clientWidth - thumb.offsetWidth - 2, d.left + dx));
    const nearest = centre => open(seg).reduce((a, b) => Math.abs(b.offsetLeft + b.offsetWidth / 2 - centre) < Math.abs(a.offsetLeft + a.offsetWidth / 2 - centre) ? b : a);
    let drag = null;
    seg.addEventListener('pointerdown', e => {   // only the chosen option's thumb can be dragged; a tap on another option chooses it
      const b = e.target.closest('button');
      drag = b && e.button === 0 && b.getAttribute('aria-pressed') === 'true' ? {id: e.pointerId, x0: e.clientX, left: b.offsetLeft, moved: false} : null;
    });
    seg.addEventListener('pointermove', e => {
      if (!drag || e.pointerId !== drag.id) return;
      const dx = e.clientX - drag.x0;
      if (!drag.moved) { if (Math.abs(dx) < 5) return; drag.moved = true; seg.classList.add('dragging'); try { seg.setPointerCapture(e.pointerId); } catch {} }
      const x = thumbX(drag, dx); thumb.style.transform = `translateX(${x}px)`;
      seg.dispatchEvent(new CustomEvent('glass:near', {detail: nearest(x + thumb.offsetWidth / 2)}));
    });
    seg.addEventListener('pointerup', e => {
      if (!drag || e.pointerId !== drag.id) return;
      const d = drag; drag = null; if (!d.moved) return;
      seg.classList.remove('dragging');
      const best = nearest(thumbX(d, e.clientX - d.x0) + thumb.offsetWidth / 2);
      seg.dispatchEvent(new CustomEvent('glass:near', {detail: null}));
      if (best.getAttribute('aria-pressed') === 'true') sync(true); else best.click();
      swallowClick = true; setTimeout(() => { swallowClick = false; }, 0);   // the browser's own click at the end of a drag
    });
    seg.addEventListener('pointercancel', e => {
      if (drag && e.pointerId === drag.id) { drag = null; seg.classList.remove('dragging'); seg.dispatchEvent(new CustomEvent('glass:near', {detail: null})); sync(true); }
    });
    seg.addEventListener('click', e => { if (swallowClick) { e.stopImmediatePropagation(); e.preventDefault(); } }, true);
    seg.addEventListener('keydown', e => {
      const buttons = [...seg.querySelectorAll('button')], i = buttons.indexOf(document.activeElement);
      if (i < 0 || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
      const list = open(seg); let next;
      if (e.key === 'Home') next = list[0]; else if (e.key === 'End') next = list.at(-1);
      else { const step = e.key === 'ArrowRight' ? 1 : -1; let k = i + step; while (buttons[k] && buttons[k].getAttribute('aria-disabled') === 'true') k += step; next = buttons[k]; }   // skip options not open now
      e.preventDefault(); if (next && next !== buttons[i]) { next.focus(); next.click(); }
    });
    new ResizeObserver(() => sync(true)).observe(seg);
  }
  function init(root = document) {
    for (const seg of root.querySelectorAll('.seg.slide')) if (!thumbs.has(seg)) { segs.push(seg); enhance(seg); }
    sync(true);
  }
  return {init, sync};
})();
