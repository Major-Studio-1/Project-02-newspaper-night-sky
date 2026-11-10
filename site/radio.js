/* Newspaper Night Sky · the radio, shared by the Radio page, Pulses and the telescope.
   A voice reads a printed passage after a greeting to the paper's town and date, over sounds of the town.
   Everything happens in the visitor's browser: the voice is the browser's own (Web Speech API) and the sounds are
   synthesised (Web Audio API). Nothing is sent anywhere, there are no sound files, and nothing costs anything to play.
   The sounds are atmosphere, not recordings of the time. The police siren in New York is a deliberate anachronism.

   Radio.say(item, options) reads one item: {date: 'YYYY-MM-DD', place: 'Philadelphia, Pa.', paper, title, text, war}.
     options: {greet: true for the "Good morning" opening, previous: the item read before, mode: 'full' | 'title' | 'intro', chime,
     rate: a number, or a function read before each sentence so the voice follows a speed control}
     It resolves to true when the item was read to the end, false when something else interrupted it.
   Radio.unlock() must run inside a click, tap or key press: browsers only start sound after one.
   Radio.onCaption(state) is called as reading moves on: {item, intro, lines, index}; index -1 means the intro. */
(() => {
'use strict';
const synth = window.speechSynthesis || null;
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
  'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'];
const TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'];
const ORD = {one: 'first', two: 'second', three: 'third', five: 'fifth', eight: 'eighth', nine: 'ninth', twelve: 'twelfth'};

// ---- Words: dates read the way an announcer would say them ----
const words = n => n < 20 ? ONES[n] : TENS[Math.floor(n / 10)] + (n % 10 ? '-' + ONES[n % 10] : '');
function ordinal(n) {
  const parts = words(n).split('-'), last = parts.pop();
  return [...parts, ORD[last] || (last.endsWith('y') ? last.slice(0, -1) + 'ieth' : last + 'th')].join('-');
}
const yearWords = y => words(Math.floor(y / 100)) + ' ' + (y % 100 === 0 ? 'hundred' : y % 100 < 10 ? 'oh ' + words(y % 100) : words(y % 100));
function parts(iso) { const [y, m, d] = iso.split('-').map(Number); return {y, m, d, wd: new Date(Date.UTC(y, m - 1, d)).getUTCDay()}; }
function spokenDate(iso, weekday = true) {
  const {y, m, d, wd} = parts(iso);
  return (weekday ? DAYS[wd] + ', ' : '') + 'the ' + ordinal(d) + ' of ' + MONTHS[m - 1] + ', ' + yearWords(y);
}
const writtenDate = iso => { const {y, m, d, wd} = parts(iso); return `${DAYS[wd]} ${d} ${MONTHS[m - 1]} ${y}`; };
const town = place => String(place || '').split(',')[0].replace(/-/g, ' ').trim();
const paperName = name => String(name || '').replace(/\s*·\s*sn\w+$/, '').trim();   // "Virginia Gazette · sn84024739": the catalogue number is for the eye
const the = name => /^the\s/i.test(name) ? name.replace(/^the/i, 'The') : 'the ' + name;

// A machine transcription, made readable aloud: no cut marks, no line-end hyphens, capitals read as words.
function clean(text) {
  return String(text || '').replace(/ſ/g, 's').replace(/&c\.?/g, 'et cetera').replace(/&/g, ' and ')
    .replace(/(\w)-\s+(\w)/g, '$1$2')
    .replace(/\s*(?:…|\.{3,})\s*/g, ' … ')
    .replace(/[*|•■¶§†‡_~^<>{}[\]]/g, ' ')
    .replace(/\b[A-Z](?: [A-Z]){2,}\b/g, w => w.replace(/ /g, ''))   // "S I R", spaced out in print, is one word
    .replace(/\b([A-Z][A-Z'’-]{2,})\b/g, w => w[0] + w.slice(1).toLowerCase())
    .replace(/\s+/g, ' ').trim().replace(/^(?:…\s*)+/, '').replace(/(?:\s*…)+$/, '').trim();
}
// Sentences, each short enough that every browser reads it to the end (Chrome stops long utterances after about 15 s).
function chunks(text, max = 170) {
  const out = [];
  for (const s of text.split(/(?<=[.!?;])\s+(?=["“'‘(]?[A-Z0-9])/)) {
    let rest = s.trim();
    while (rest.length > max) {
      let cut = rest.lastIndexOf(', ', max); if (cut < max * .4) cut = rest.lastIndexOf(' ', max); if (cut < 1) cut = max;
      out.push(rest.slice(0, cut + 1).trim()); rest = rest.slice(cut + 1).trim();
    }
    if (rest) out.push(rest);
  }
  return out;
}

// ---- The voice: the best English voice the browser offers (natural voices first), or the one the visitor picked ----
let voices = [], voice = null, voiceName = null, volume = .8;
try { voiceName = localStorage.getItem('nns-radio-voice'); volume = Number(localStorage.getItem('nns-radio-volume') ?? .8); } catch {}
if (!(volume >= 0 && volume <= 1)) volume = .8;
function loadVoices() {
  if (!synth) return;
  const score = v => (/natural|neural|online|premium|enhanced/i.test(v.name) ? 40 : 0) + (/google/i.test(v.name) ? 22 : 0)
    + (/samantha|daniel|karen|moira|serena|alex|ava|evan|zoe|aria|guy|jenny|libby|ryan|sonia|andrew|emma|brian/i.test(v.name) ? 14 : 0)
    + (/en[-_]US/i.test(v.lang) ? 4 : /en[-_]GB/i.test(v.lang) ? 3 : 0) + (v.default ? 1 : 0);
  voices = synth.getVoices().filter(v => /^en([-_]|$)/i.test(v.lang)).sort((a, b) => score(b) - score(a) || a.name.localeCompare(b.name));
  voice = voices.find(v => v.name === voiceName) || voices[0] || null;
  listeners.voices.forEach(f => f(voices));
}
const listeners = {voices: [], caption: [], state: [], live: []};
if (synth) { loadVoices(); if (synth.addEventListener) synth.addEventListener('voiceschanged', loadVoices); else synth.onvoiceschanged = loadVoices; }

let session = 0, speaking = false, unlocked = false;
function speakOne(text, rate) {
  return new Promise(resolve => {
    if (!synth || !voices.length) return setTimeout(() => resolve(true), Math.max(1200, text.split(' ').length * 330 / rate));   // no voice: the words are shown for as long as reading them would take
    const u = new SpeechSynthesisUtterance(text);
    if (voice) { u.voice = voice; u.lang = voice.lang; } else u.lang = 'en-US';
    u.rate = rate; u.pitch = 1; u.volume = volume;
    let done = false;
    const finish = ok => { if (done) return; done = true; clearTimeout(watch); resolve(ok); };
    // Stopped on purpose: at once. Not allowed yet (no touch so far) or failed: the words stay up for their reading time.
    u.onend = () => finish(true);
    u.onerror = e => ['interrupted', 'canceled'].includes(e.error) ? finish(false) : setTimeout(() => finish(true), Math.max(1200, text.split(' ').length * 330 / rate));
    const watch = setTimeout(() => finish(true), 5000 + text.length * 140 / rate);   // some browsers never report the end
    synth.speak(u);
  });
}

// ---- Sounds: made in the browser. A quiet radio bed, a sound for the town, and short cues ----
let ctx = null, master = null, bed = null, townBus = null, townBed = null, crackleTimer = 0, noise = {};
function audio() {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return null;
    ctx = new AC(); master = ctx.createGain(); master.gain.value = volume; master.connect(ctx.destination);
  }
  if (ctx.state === 'suspended') ctx.resume().catch(() => {});
  return ctx;
}
function noiseBuffer(kind) {
  if (noise[kind]) return noise[kind];
  const len = ctx.sampleRate * (kind === 'click' ? .012 : 3), buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
  let last = 0;
  for (let i = 0; i < len; i++) {
    const w = Math.random() * 2 - 1;
    if (kind === 'brown') { last = (last + .02 * w) / 1.02; d[i] = last * 3.5; }
    else if (kind === 'click') d[i] = w * Math.pow(1 - i / len, 6);
    else d[i] = w;
  }
  return noise[kind] = buf;
}
function source(kind, loop = true) { const s = ctx.createBufferSource(); s.buffer = noiseBuffer(kind); s.loop = loop; return s; }
function filter(type, freq, q = .7) { const f = ctx.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q; return f; }
function gain(v) { const g = ctx.createGain(); g.gain.value = v; return g; }
function startBed() {
  if (!audio() || bed) return;
  bed = gain(0); bed.connect(master);
  const hiss = source('white'); hiss.connect(filter('bandpass', 2600, .6)).connect(gain(.010)).connect(bed); hiss.start();
  const hum = ctx.createOscillator(); hum.frequency.value = 60; hum.connect(gain(.0035)).connect(bed); hum.start();
  bed.gain.setTargetAtTime(1, ctx.currentTime, .5);
  townBus = gain(1); townBus.connect(master);
  crackleTimer = setInterval(() => {   // the crackle of an old set
    if (!ctx || ctx.state !== 'running' || Math.random() > .3) return;
    const s = source('click', false); s.connect(filter('highpass', 1800)).connect(gain(.012 + Math.random() * .04)).connect(bed); s.start(ctx.currentTime + Math.random() * .1);
  }, 150);
}
function stopBed() {
  clearInterval(crackleTimer); crackleTimer = 0;
  for (const g of [bed, townBus]) if (g) { g.gain.setTargetAtTime(0, ctx.currentTime, .25); const old = g; setTimeout(() => old.disconnect(), 1500); }
  bed = townBus = townBed = null;
}
// Which sounds suit a town: a harbour, a busy street or the country. New York keeps its siren.
const SEA = /^(Portland|Portsmouth|Newburyport|Salem|Boston|Providence|Warren|Newport|New York|Philadelphia|Wilmington|Alexandria|Norfolk|Charleston|Baltimore)$/;
const STREET = /^(Boston|New York|Philadelphia|Charleston|Washington|Richmond|Baltimore|Hartford|Lexington)$/;
function scheme(name) {
  if (name === 'New York') return {bed: 'city', cue: 'siren'};
  return {bed: SEA.test(name) ? 'sea' : STREET.test(name) ? 'city' : 'country', cue: STREET.test(name) ? 'hooves' : SEA.test(name) ? 'ship' : 'birds'};
}
function setTownBed(kind) {
  if (!ctx || !townBus || townBed?.kind === kind) return;
  if (townBed) { const old = townBed; old.g.gain.setTargetAtTime(0, ctx.currentTime, .6); setTimeout(() => { old.stop(); old.g.disconnect(); }, 3000); }
  const g = gain(0), stops = [];
  if (kind === 'sea') {   // water against a wharf: low noise that swells and falls
    const s = source('brown'), f = filter('lowpass', 520), swell = gain(.5), lfo = ctx.createOscillator(), depth = gain(.45);
    lfo.frequency.value = .11; lfo.connect(depth).connect(swell.gain); s.connect(f).connect(swell).connect(g); s.start(); lfo.start(); stops.push(s, lfo);
  } else if (kind === 'city') {   // the murmur of a street
    const s = source('brown'), f = filter('lowpass', 300); s.connect(f).connect(gain(.8)).connect(g); s.start(); stops.push(s);
  } else {   // the country: a faint air
    const s = source('brown'), f = filter('lowpass', 180); s.connect(f).connect(gain(.35)).connect(g); s.start(); stops.push(s);
  }
  g.connect(townBus); g.gain.setTargetAtTime(.09, ctx.currentTime, .8);
  townBed = {kind, g, stop: () => stops.forEach(s => { try { s.stop(); } catch {} })};
}
function duck(on) { if (townBus && ctx) townBus.gain.setTargetAtTime(on ? .45 : 1, ctx.currentTime, .3); }
// Bell-like tones from inharmonic partials.
function bell(at, base, ratios, decay, level, out) {
  for (const [k, r] of ratios.entries()) {
    const o = ctx.createOscillator(), g = gain(0); o.frequency.value = base * r; o.connect(g).connect(out);
    g.gain.setValueAtTime(0, at); g.gain.linearRampToValueAtTime(level / (k + 1.2), at + .006); g.gain.exponentialRampToValueAtTime(.0001, at + decay * (1.2 - k * .08));
    o.start(at); o.stop(at + decay * 1.3);
  }
}
function cue(kind) {
  if (!ctx || ctx.state !== 'running') return 0;
  const t = ctx.currentTime + .05, far = filter('lowpass', 2600); far.connect(townBus || master);
  const pan = ctx.createStereoPanner ? ctx.createStereoPanner() : null, out = pan ? (pan.connect(far), pan) : far;
  if (kind === 'chime') {   // the station's own call: a gentle rising arpeggio
    const o = filter('lowpass', 5000); o.connect(master);
    [440, 554.37, 659.25, 880].forEach((f, i) => bell(t + i * .26, f, [1, 2, 3.01], 1.6, .05, o));
    return 1600;
  }
  if (kind === 'sweep') {   // turning the dial between stations
    const s = source('white'), f = filter('bandpass', 400, 4), g = gain(0); s.connect(f).connect(g).connect(master);
    f.frequency.setValueAtTime(350, t); f.frequency.exponentialRampToValueAtTime(3200, t + .7);
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.05, t + .12); g.gain.linearRampToValueAtTime(0, t + .85); s.start(t); s.stop(t + .9);
    const w = ctx.createOscillator(), wg = gain(0); w.frequency.setValueAtTime(1500, t); w.frequency.exponentialRampToValueAtTime(700, t + .8);
    w.connect(wg).connect(master); wg.gain.setValueAtTime(0, t); wg.gain.linearRampToValueAtTime(.006, t + .2); wg.gain.linearRampToValueAtTime(0, t + .85); w.start(t); w.stop(t + .9);
    return 900;
  }
  if (kind === 'church') { for (let i = 0; i < 3; i++) bell(t + i * 2.1, 196, [.5, 1, 1.183, 1.506, 2, 2.514, 2.662], 4, .07, out); return 1200; }
  if (kind === 'ship') { for (const k of [0, .38, 1.4, 1.78]) bell(t + k, 1046, [1, 2.0, 2.76, 5.4], 1.4, .05, out); return 600; }
  if (kind === 'siren') {   // a distant wail moving across the city
    const o = ctx.createOscillator(), f = filter('lowpass', 1500), g = gain(0); o.type = 'sawtooth';
    o.frequency.setValueAtTime(620, t);
    for (let k = 0; k < 3; k++) { o.frequency.linearRampToValueAtTime(1180, t + k * 2.6 + 1.3); o.frequency.linearRampToValueAtTime(620, t + k * 2.6 + 2.6); }
    o.connect(f).connect(g).connect(out); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.02, t + 1.5); g.gain.linearRampToValueAtTime(.02, t + 5.5); g.gain.linearRampToValueAtTime(0, t + 7.8);
    if (pan) { pan.pan.setValueAtTime(-.7, t); pan.pan.linearRampToValueAtTime(.6, t + 7.8); }
    o.start(t); o.stop(t + 8); return 700;
  }
  if (kind === 'hooves') {   // a horse and cart passing
    const g = gain(0); g.connect(out);
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.9, t + 1.6); g.gain.linearRampToValueAtTime(0, t + 4.6);
    if (pan) { pan.pan.setValueAtTime(.8, t); pan.pan.linearRampToValueAtTime(-.8, t + 4.6); }
    for (let k = 0, at = t; at < t + 4.6; k++) {
      const s = source('click', false), f = filter('bandpass', 700 + 300 * (k % 2), 2), o = ctx.createOscillator(), og = gain(0);
      s.connect(f).connect(gain(.5)).connect(g); s.start(at);
      o.frequency.value = 180 + 60 * (k % 2); o.connect(og).connect(g); og.gain.setValueAtTime(.12, at); og.gain.exponentialRampToValueAtTime(.0001, at + .07); o.start(at); o.stop(at + .08);
      at += k % 2 ? .23 : .13;
    }
    return 500;
  }
  if (kind === 'birds') {   // morning birds
    for (let n = 0; n < 3; n++) {
      const at0 = t + n * 1.3 + Math.random() * .5, base = 2600 + Math.random() * 1600;
      for (let k = 0; k < 3; k++) {
        const o = ctx.createOscillator(), g = gain(0), at = at0 + k * .14; o.frequency.setValueAtTime(base, at); o.frequency.exponentialRampToValueAtTime(base * 1.5, at + .07);
        o.connect(g).connect(out); g.gain.setValueAtTime(0, at); g.gain.linearRampToValueAtTime(.025, at + .02); g.gain.linearRampToValueAtTime(0, at + .09); o.start(at); o.stop(at + .1);
      }
    }
    return 500;
  }
  if (kind === 'drum') {   // a distant drum, under war news
    const pattern = [0, .18, .36, .9, 1.08, 1.26, 1.8, 2.25];
    for (const k of pattern) {
      const s = source('white', false), f = filter('bandpass', 1300, .8), g = gain(0); s.connect(f).connect(g).connect(out);
      g.gain.setValueAtTime(.08, t + k); g.gain.exponentialRampToValueAtTime(.0001, t + k + .12); s.start(t + k); s.stop(t + k + .14);
    }
    return 400;
  }
  if (kind === 'scratch') {   // a record pulled back and forth under the hand: two quick strokes of noise and a bent tone
    const s = source('white', false), bp = filter('bandpass', 900, 3), g = gain(0); s.connect(bp).connect(g).connect(master);
    for (const [at, dur, f0, f1] of [[0, .085, 650, 2700], [.095, .1, 2500, 480]]) {
      bp.frequency.setValueAtTime(f0, t + at); bp.frequency.exponentialRampToValueAtTime(f1, t + at + dur);
      g.gain.setValueAtTime(0, t + at); g.gain.linearRampToValueAtTime(.075, t + at + .012); g.gain.linearRampToValueAtTime(0, t + at + dur);
    }
    s.start(t); s.stop(t + .21);
    const o = ctx.createOscillator(), og = gain(0); o.type = 'triangle';
    o.frequency.setValueAtTime(210, t); o.frequency.exponentialRampToValueAtTime(540, t + .085); o.frequency.exponentialRampToValueAtTime(150, t + .19);
    o.connect(og).connect(master); og.gain.setValueAtTime(0, t); og.gain.linearRampToValueAtTime(.022, t + .02); og.gain.linearRampToValueAtTime(0, t + .2); o.start(t); o.stop(t + .21);
    return 210;
  }
  if (kind === 'tune') {   // turning the dial: a breath of static and the whistle of a station drifting past
    const s = source('white', false), f = filter('bandpass', 1500, 1.1), g = gain(0); s.connect(f).connect(g).connect(master);
    f.frequency.setValueAtTime(700, t); f.frequency.exponentialRampToValueAtTime(2600, t + .42);
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.04, t + .05); g.gain.linearRampToValueAtTime(0, t + .46); s.start(t); s.stop(t + .5);
    const w = ctx.createOscillator(), wg = gain(0), f0 = 700 + Math.random() * 1300;
    w.frequency.setValueAtTime(f0, t); w.frequency.exponentialRampToValueAtTime(f0 * (Math.random() < .5 ? .45 : 2.1), t + .42);
    w.connect(wg).connect(master); wg.gain.setValueAtTime(0, t); wg.gain.linearRampToValueAtTime(.011, t + .08); wg.gain.linearRampToValueAtTime(0, t + .44); w.start(t); w.stop(t + .46);
    return 460;
  }
  if (kind === 'strings') {   // the opening: a long, soft chord of strings that swells in and slowly leaves
    const out = gain(0), lp = filter('lowpass', 600, .5); lp.connect(out); out.connect(master);
    const vib = ctx.createOscillator(), depth = gain(3.2); vib.frequency.value = 4.7; vib.connect(depth); vib.start(t); vib.stop(t + 15);
    for (const [f, level] of [[146.83, .5], [220, .38], [293.66, .32], [369.99, .15], [440, .11]]) {   // D, A, D, F sharp, A: open and warm
      for (const cents of [-5, 5]) {   // two players to a note, a little apart
        const o = ctx.createOscillator(), og = gain(level * .5); o.type = 'sawtooth'; o.frequency.value = f; o.detune.value = cents; depth.connect(o.detune);
        o.connect(og).connect(lp); o.start(t); o.stop(t + 15);
      }
    }
    out.gain.setValueAtTime(0, t); out.gain.linearRampToValueAtTime(.05, t + 3.4); out.gain.setValueAtTime(.05, t + 6.5); out.gain.linearRampToValueAtTime(0, t + 14.5);
    lp.frequency.setValueAtTime(520, t); lp.frequency.linearRampToValueAtTime(1300, t + 4.2); lp.frequency.linearRampToValueAtTime(650, t + 14);
    return 0;   // it plays under whatever follows
  }
  return 0;
}
const wait = ms => new Promise(r => setTimeout(r, ms));

// ---- Reading one item ----
function intro(item, greet, previous) {
  const name = town(item.place), paper = paperName(item.paper);
  if (greet) return {lines: [`Good morning, ${name}!`, `It is ${spokenDate(item.date)}.`, paper ? `From ${the(paper)}.` : ''].filter(Boolean)};
  const sameDay = previous && previous.date === item.date, sameTown = sameDay && town(previous.place) === name;
  const where = paper ? `${sameTown ? 'Also in' : 'In'} ${name}, ${the(paper)}.` : `In ${name}.`;
  return {lines: [sameDay ? where : `${spokenDate(item.date, false).replace(/^the /, 'The ')}. ${where}`]};
}
async function say(item, {greet = false, previous = null, rate = 1, mode = 'full', chime = false} = {}) {
  const my = ++session; if (synth) synth.cancel();
  const pace = () => typeof rate === 'function' ? rate() : rate;
  const live = () => my === session;
  startBed();
  const name = town(item.place), sc = scheme(name), head = intro(item, greet, previous);
  const body = mode === 'intro' ? '' : mode === 'title' ? clean(item.title) : clean(item.text || item.title);
  const lines = body ? chunks(body) : [];
  const show = index => listeners.caption.forEach(f => f({item, intro: head.lines.join(' '), lines, index}));
  speaking = true; listeners.state.forEach(f => f('speaking'));
  try {
    show(-1);
    if (chime) await wait(cue('chime'));
    else if (!greet && live()) await wait(cue('tune'));
    if (!live()) return false;
    if (greet) cue('church');
    setTownBed(sc.bed);
    duck(true);
    for (const [k, line] of head.lines.entries()) {
      if (!live()) return false;
      if (k === head.lines.length - 1) cue(item.war ? 'drum' : sc.cue);   // the town's own sound, under the paper's name
      await speakOne(line, Math.min(1.3, pace()));
    }
    await wait(250);
    for (let i = 0; i < lines.length; i++) {
      if (!live()) return false;
      show(i);
      await speakOne(lines[i], pace());
    }
    if (!live()) return false;
    duck(false); await wait(700);
    return live();
  } finally {
    if (live()) { speaking = false; listeners.state.forEach(f => f('idle')); }
  }
}
// One spoken line of the radio's own, such as where else a story was printed.
async function sayLine(text, {rate = 1, head = ''} = {}) {
  const my = ++session; if (synth) synth.cancel();
  const live = () => my === session, lines = chunks(clean(text));
  startBed(); speaking = true; listeners.state.forEach(f => f('speaking'));
  try {
    for (let i = 0; i < lines.length; i++) {
      if (!live()) return false;
      listeners.caption.forEach(f => f({item: null, intro: head, lines, index: i}));
      await speakOne(lines[i], typeof rate === 'function' ? rate() : rate);
    }
    await wait(500);
    return live();
  } finally {
    if (live()) { speaking = false; listeners.state.forEach(f => f('idle')); }
  }
}
function stop(silence = false) {
  session++; if (synth) synth.cancel(); speaking = false; duck(false);
  if (silence) { liveStopAll({scratch: false}); stopBed(); }
  listeners.state.forEach(f => f(silence ? 'off' : 'idle'));
}

// ---- Voices on demand: each star or paper the visitor activates speaks in its own voice ----
// A voice starts only when the visitor activates something: pointing at a star or a paper, clicking it, selecting an
// area, or searching. Nothing speaks on its own while time drifts or plays. Several activated at once speak at once
// (up to five), because they arrive as sound the page can mix: eSpeak (radio-voices.js, a worker), placed left or right
// by where each story was printed and heard like a distant set in a small room. Moving on to another star stops the old
// voice the way a hand stops a record (it slows, drops and fades, with a scratch) and spins the new one up. The browser's
// own voice, which can say one thing at a time, stays for the Radio page. Nothing loads until the first voice is wanted.
const LIVE_MAX = 5;
let liveWorker = null, liveReady = null, liveSeq = 0, liveBus = null, scratchAt = 0;
const liveWaiting = new Map(), live = new Map();   // key -> {src, g, label, text, ending}
function liveStart() {
  if (liveReady) return liveReady;
  liveReady = new Promise(resolve => {
    try { liveWorker = new Worker(new URL('radio-voices.js', document.baseURI), {type: 'module'}); } catch { resolve(false); return; }
    liveWorker.onmessage = e => { const w = liveWaiting.get(e.data.id); if (w) { liveWaiting.delete(e.data.id); w(e.data); } };
    liveWorker.onerror = () => resolve(false);
    liveRender('Good morning.', {speed: 175}).then(out => resolve(!out.error));   // loads eSpeak once
  });
  liveReady.then(ok => { if (!ok) liveReady = null; });
  return liveReady;
}
function liveRender(text, opts) {
  return new Promise(resolve => {
    const id = ++liveSeq; liveWaiting.set(id, resolve); liveWorker.postMessage({id, text, opts});
    setTimeout(() => { if (liveWaiting.delete(id)) resolve({error: 'timeout'}); }, 8000);
  });
}
const liveChanged = () => listeners.live.forEach(f => f([...live.entries()].filter(([, v]) => !v.ending).map(([key, v]) => ({key, label: v.label, text: v.text}))));
function roomImpulse(c) {   // a small room: a second and a half of decaying noise
  const len = Math.round(c.sampleRate * 1.5), b = c.createBuffer(2, len, c.sampleRate);
  for (let ch = 0; ch < 2; ch++) { const d = b.getChannelData(ch); for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3.4); }
  return b;
}
function liveOut(c) {
  if (liveBus) return liveBus;
  liveBus = gain(1);
  const squeeze = c.createDynamicsCompressor(); squeeze.threshold.value = -18; squeeze.ratio.value = 3.5;
  liveBus.connect(filter('highpass', 220)).connect(filter('lowpass', 4200)).connect(squeeze).connect(master);
  const room = c.createConvolver(); room.buffer = roomImpulse(c); squeeze.connect(room).connect(gain(.16)).connect(master);
  return liveBus;
}
async function livePlay(key, text, {pan = 0, wpm = 165, variant = 'm1', pitch = 50, level = .8, label = '', spin = true} = {}) {
  const c = audio(); if (!c || c.state !== 'running' || !text) return false;
  const now = live.get(key); if (now && !now.ending) return true;   // already speaking
  const speaking = [...live.entries()].filter(([, v]) => !v.ending);
  if (speaking.length >= LIVE_MAX) liveStop(speaking[0][0]);   // the oldest gives way
  const entry = {src: null, g: null, label, text: clean(text), ending: false};
  live.set(key, entry); liveChanged(); startBed();
  const gone = () => live.get(key) !== entry || entry.ending;
  try {
    if (!(await liveStart()) || gone()) return false;
    const out = await liveRender(entry.text, {speed: Math.round(wpm), variant, pitch});
    if (out.error || gone()) return false;
    const buf = await c.decodeAudioData(out.buf);
    if (gone()) return false;
    const src = c.createBufferSource(), g = gain(0), p = c.createStereoPanner ? c.createStereoPanner() : null, t = c.currentTime;
    src.buffer = buf;
    if (spin) { src.playbackRate.setValueAtTime(.55, t); src.playbackRate.exponentialRampToValueAtTime(1, t + .22); }   // spun up, like a record let go
    if (p) { p.pan.value = Math.max(-1, Math.min(1, pan)); src.connect(g).connect(p).connect(liveOut(c)); } else src.connect(g).connect(liveOut(c));
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(level, t + .08);
    entry.src = src; entry.g = g;
    return await new Promise(resolve => {
      src.onended = () => { if (live.get(key) === entry) { live.delete(key); liveChanged(); } resolve(!entry.ending); };
      src.start(t);
    });
  } catch { return false; }
  finally { if (live.get(key) === entry && !entry.src) { live.delete(key); liveChanged(); } }
}
// Stopping a voice: like a hand on a record, it slows, drops in pitch and fades, with a scratch.
function liveStop(key, {scratch = true} = {}) {
  const e = live.get(key); if (!e || e.ending) return;
  e.ending = true; liveChanged();
  if (!e.src) { live.delete(key); return; }   // still being made: it never starts
  const t = ctx.currentTime;
  try {
    e.src.playbackRate.cancelScheduledValues(t); e.src.playbackRate.setValueAtTime(Math.max(.2, e.src.playbackRate.value), t); e.src.playbackRate.exponentialRampToValueAtTime(.16, t + .34);
    e.g.gain.cancelScheduledValues(t); e.g.gain.setValueAtTime(e.g.gain.value, t); e.g.gain.linearRampToValueAtTime(0, t + .36);
    e.src.stop(t + .4);
  } catch {}
  if (scratch && performance.now() - scratchAt > 140) { scratchAt = performance.now(); cue('scratch'); }   // one scratch for several stopped together
}
function liveStopAll(opts) { for (const k of [...live.keys()]) liveStop(k, opts); }
// A paper or a town keeps one voice: the same variant and pitch every time it speaks.
const VARIANTS = ['m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'f1', 'f2', 'f3', 'f4'];
function voiceOf(key) {
  let h = 2166136261; for (const ch of String(key)) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
  h >>>= 0; return {variant: VARIANTS[h % VARIANTS.length], pitch: 34 + (h >>> 8) % 34};
}
const firstWords = (text, n) => { const w = clean(text).split(' '); return w.slice(0, n).join(' ') + (w.length > n ? '…' : ''); };
// Browsers allow sound only after a click, tap or key press: call this inside one. It returns whether sound can play now.
function unlock() {
  if (!audio()) return false;
  const active = navigator.userActivation ? navigator.userActivation.isActive : true;
  if (synth && active && !unlocked) { unlocked = true; const u = new SpeechSynthesisUtterance(' '); u.volume = 0; synth.speak(u); }   // wakes speech on phones
  return ctx.state === 'running';
}

window.Radio = {
  get supported() { return !!synth; },
  get hasVoice() { return voices.length > 0; },
  get speaking() { return speaking; },
  get unlocked() { return !!ctx && ctx.state === 'running'; },
  get voice() { return voice; },
  get voices() { return voices; },
  get volume() { return volume; },
  setVolume(v) { volume = Math.max(0, Math.min(1, v)); if (master) master.gain.setTargetAtTime(volume, ctx.currentTime, .05); try { localStorage.setItem('nns-radio-volume', String(volume)); } catch {} },
  nextVoice() {
    if (!voices.length) return null;
    voice = voices[(voices.indexOf(voice) + 1) % voices.length]; voiceName = voice.name;
    try { localStorage.setItem('nns-radio-voice', voiceName); } catch {}
    return voice;
  },
  onCaption(f) { listeners.caption.push(f); }, onState(f) { listeners.state.push(f); }, onVoices(f) { listeners.voices.push(f); },
  say, sayLine, stop, unlock, cue: k => { audio(); return cue(k); },
  live: {
    play: livePlay, stop: liveStop, stopAll: liveStopAll, has: key => !!live.get(key) && !live.get(key).ending,
    preload: () => { if (audio() && ctx.state === 'running') liveStart(); },
    get count() { return [...live.values()].filter(v => !v.ending).length; }, onChange(f) { listeners.live.push(f); }, voiceOf, firstWords, MAX: LIVE_MAX
  },
  spokenDate, writtenDate, town, paperName, clean, chunks, intro
};
})();
