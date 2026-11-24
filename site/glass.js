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

/* The receipt line (Telescope and Pulses, since 23 November 2026, at the owner's word of 11 November): one line of plain
   words over the instrument that says what is shown: the evidence, the years, which stories, how they are placed and
   their colour. Each part is a button that opens its own step in place, a glass card under the part (on a phone, a sheet
   from the foot of the screen). One step is open at a time; the part again, ✕ or Esc closes it. The line is also the
   link to exactly this view (Copy link), and in Watch the same words are the caption, with nothing to press. Styles in
   site.css.
   Receipt.mount(host, cfg) fills host; Receipt.update(host, cfg) re-words it and leaves an open step open.
   cfg = {lead, parts: [{key, text, title, step}], link, caption}. A part's step is {title, node, wide}: an element of the
   page, shown in the card and put back where it was when the card closes, so its controls keep their listeners; or
   {glow, focus}: the control is already on the screen, so it glows and takes the focus instead.
   Receipt.peek(host, key, {ms, done}) opens a step for a moment and folds it back into its part, which glows: a first
   visit's hint of what the part holds. A visitor who reaches into the card keeps it open. */
window.Receipt = (() => {
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  const LINK = '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M6.6 9.4a2.6 2.6 0 0 0 3.7 0l2.5-2.5a2.6 2.6 0 0 0-3.7-3.7l-.9.9"/><path d="M9.4 6.6a2.6 2.6 0 0 0-3.7 0L3.2 9.1a2.6 2.6 0 0 0 3.7 3.7l.9-.9"/></svg>';
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  let now = null;   // the open step: {host, part, card, key, node, home, next, timer, peek, done}
  const glow = t => { t.classList.remove('rc-glow'); void t.offsetWidth; t.classList.add('rc-glow'); clearTimeout(t._glow); t._glow = setTimeout(() => t.classList.remove('rc-glow'), 1700); };
  function close(how) {
    const o = now; if (!o) return; now = null; clearTimeout(o.timer);
    if (o.node) { if (o.next && o.next.parentNode === o.home) o.home.insertBefore(o.node, o.next); else o.home.append(o.node); }
    o.card.remove(); o.part.setAttribute('aria-expanded', 'false');
    if (how === 'key' || how === 'x') o.part.focus({preventScroll: true});
    if (o.done) { const d = o.done; o.done = null; setTimeout(d, 300); }
  }
  // Under its part, inside the line; a wide step spans the line; on a phone every step is a sheet (site.css).
  function place(o) {
    const {card, part, host} = o; card.style.left = ''; card.style.maxHeight = '';
    if (innerWidth <= 640) return;
    card.style.maxHeight = Math.max(180, innerHeight - card.getBoundingClientRect().top - 12) + 'px';   // the whole card on the screen, also inside a sticky bar
    if (card.classList.contains('wide')) return;
    const hr = host.getBoundingClientRect(), pr = part.getBoundingClientRect();
    card.style.left = Math.max(8, Math.min(pr.left - hr.left - 10, hr.width - card.offsetWidth - 8)) + 'px';
  }
  function open(host, part, how) {
    const cfg = host._cfg, p = cfg && cfg.parts.find(x => x.key === part.dataset.key), s = p && p.step;
    if (!s) return;
    close();
    if (s.glow) {   // the control is already on the screen: point at it
      const t = typeof s.glow === 'string' ? document.querySelector(s.glow) : s.glow; if (!t) return;
      glow(t); t.scrollIntoView({block: 'nearest'});
      const f = s.focus && document.querySelector(s.focus); if (f) f.focus({preventScroll: true});
      return;
    }
    const card = el('div', 'rc-step' + (s.wide ? ' wide' : '')); card.id = (host.id || 'rc') + '-step'; card.setAttribute('role', 'group'); card.setAttribute('aria-label', s.title);
    const head = el('div', 'rc-step-head'), x = el('button', 'rc-x', '✕'); x.type = 'button'; x.title = 'Close (Esc)'; x.setAttribute('aria-label', 'Close');
    head.append(el('span', 'rc-step-h', s.title), x); card.append(head);
    const o = {host, part, card, key: p.key};
    const n = typeof s.node === 'string' ? document.querySelector(s.node) : s.node;
    if (n) { o.node = n; o.home = n.parentNode; o.next = n.nextSibling; card.append(n); }
    x.addEventListener('click', () => close('x'));
    host.append(card); now = o; part.setAttribute('aria-expanded', 'true'); part.setAttribute('aria-controls', card.id);
    place(o);
    if (window.Glass) Glass.init(card);
    if (cfg.onOpen) cfg.onOpen(card, p.key);
    if (how === 'key') { const f = card.querySelector('button[aria-pressed="true"]:not([aria-disabled="true"]), .rc-body button, .rc-body input, .rc-body a'); (f || x).focus(); }
  }
  // The card folds back into its part, which glows: this is where it lives.
  function fold(o) {
    const done = o.done; o.done = null;
    const end = () => { if (now === o) close(); glow(o.part); if (done) setTimeout(done, 900); };
    if (reduced()) { end(); return; }
    const cr = o.card.getBoundingClientRect(), pr = o.part.getBoundingClientRect();
    o.card.style.transformOrigin = `${pr.left + pr.width / 2 - cr.left}px ${pr.top + pr.height / 2 - cr.top}px`;
    o.card.classList.add('rc-fold'); setTimeout(end, 480);
  }
  function peek(host, key, {ms = 6000, done} = {}) {
    const part = host.querySelector(`.rc-part[data-key="${key}"]`);
    if (!part || !part.offsetWidth || now) { if (done) done(); return; }
    open(host, part, '');
    const o = now; if (!o || o.part !== part) { if (done) done(); return; }
    o.peek = true; o.done = done;
    const stay = () => { if (now === o && o.peek) { o.peek = false; clearTimeout(o.timer); } };
    // A visitor's own touch, pointer, wheel or key (not "scroll": the shelf's rail scrolls by itself as the card appears).
    for (const t of ['pointerdown', 'pointerenter', 'focusin', 'wheel', 'touchstart', 'keydown']) o.card.addEventListener(t, stay, {passive: true, capture: true});
    o.timer = setTimeout(() => { if (now === o && o.peek) fold(o); }, ms);
  }
  // New words for the same parts: the open step stays open (and moves if the line wrapped differently).
  function update(host, cfg) {
    host._cfg = cfg;
    for (const p of cfg.parts) {
      const b = host.querySelector(`.rc-part[data-key="${p.key}"]`); if (!b) continue;
      if (b.textContent !== p.text) b.textContent = p.text;
      if (b.tagName === 'BUTTON' && p.title && b.title !== p.title) b.title = p.title;
    }
    if (now && now.host === host) place(now);
  }
  async function copy(host, a) {
    const url = new URL(host._cfg.link, location.href).href, lbl = a.querySelector('.lbl');
    let ok = false;
    try { await navigator.clipboard.writeText(url); ok = true; } catch {
      const t = el('textarea'); t.value = url; t.setAttribute('readonly', ''); t.style.cssText = 'position:fixed;left:-9999px;top:0'; document.body.append(t); t.select();
      try { ok = document.execCommand('copy'); } catch {} t.remove();
    }
    // The address bar holds the same link, so a browser that will not copy can still give it.
    lbl.textContent = ok ? 'Copied' : 'Copy it from the address bar';
    setTimeout(() => { lbl.textContent = 'Copy link'; }, ok ? 1800 : 4000);
  }
  function mount(host, cfg) {
    host.classList.add('rc'); host.classList.toggle('rc-caption', !!cfg.caption); host.replaceChildren(); host._cfg = cfg;   // not "caption": the Telescope's search card has that class
    host.setAttribute('role', 'region'); host.setAttribute('aria-label', 'What is shown');
    const line = el('div', 'rc-line'); host.append(line);
    if (cfg.lead) line.append(el('span', 'rc-lead', cfg.lead));
    cfg.parts.forEach((p, i) => {   // each part with the dot after it, so a wrapped line ends with a dot rather than starts with one
      const item = el('span', 'rc-item'), b = el(cfg.caption ? 'span' : 'button', 'rc-part', p.text); b.dataset.key = p.key;
      if (!cfg.caption) {
        b.type = 'button'; b.title = p.title || 'Change this';
        if (p.step && !p.step.glow) b.setAttribute('aria-expanded', 'false');
        b.addEventListener('click', e => now && now.part === b ? close() : open(host, b, e.detail === 0 ? 'key' : ''));
      }
      item.append(b);
      if (i < cfg.parts.length - 1) { const sep = el('span', 'rc-sep', '·'); sep.setAttribute('aria-hidden', 'true'); item.append(sep); }
      line.append(item);
    });
    if (!cfg.caption && cfg.link != null) {
      const acts = el('div', 'rc-acts'), a = el('button', 'rc-link'); a.type = 'button'; a.title = 'Copy the link to exactly this view';
      a.innerHTML = LINK + '<span class="lbl" aria-live="polite">Copy link</span>';
      a.addEventListener('click', () => copy(host, a));
      acts.append(a); host.append(acts);
    }
    return host;
  }
  // Esc closes the open step first (a search box with words in it clears them first, as before).
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape' || !now) return;
    const t = e.target; if (t instanceof HTMLInputElement && t.value) return;
    e.stopPropagation(); close('key');
  }, true);
  addEventListener('resize', () => { if (now) place(now); });
  return {mount, update, peek, close: () => close(), open: (host, key) => { const b = host.querySelector(`.rc-part[data-key="${key}"]`); if (b) open(host, b, ''); },
    isOpen: key => !!now && (key == null || now.key === key)};
})();
