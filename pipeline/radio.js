/* Newspaper Night Sky · the radio, shared by the Radio page, Pulses and the telescope.
   A voice reads a printed passage after a greeting to the paper's town and date, over sounds of the town.
   Everything happens in the visitor's browser. The voices were recorded once, when the site was built (Kokoro, by
   work/audio_render.py), and play from packs of MP3s; on the Radio page a passage without a recording is read by the
   browser's own voice (Web Speech API). The sounds are synthesised (Web Audio API). Nothing is sent anywhere.
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
// A sentence is split only when it is long, at a semicolon or comma past the middle if there is one, so the voice does
// not drop as if at a full stop in the middle of a clause.
function chunks(text, max = 220) {
  const out = [];
  for (const s of text.split(/(?<=[.!?;])\s+(?=["“'‘(]?[A-Z0-9])/)) {
    let rest = s.trim();
    while (rest.length > max) {
      let cut = Math.max(rest.lastIndexOf('; ', max), rest.lastIndexOf(', ', max)); if (cut < max * .5) cut = rest.lastIndexOf(' ', max); if (cut < 1) cut = max;
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
  const edge = /\bEdg\//.test(navigator.userAgent), natural = v => /natural|neural|premium|enhanced/i.test(v.name);
  const score = v => (natural(v) && (edge || v.localService) ? 40 : 0) + (v.localService || (edge && natural(v)) ? 12 : -12)
    + (/samantha|daniel|karen|moira|serena|alex|ava|evan|zoe|aria|guy|jenny|libby|ryan|sonia|andrew|emma|brian/i.test(v.name) ? 14 : 0)
    + (/en[-_]US/i.test(v.lang) ? 4 : /en[-_]GB/i.test(v.lang) ? 3 : 0) + (v.default ? 1 : 0);
  voices = synth.getVoices().filter(v => /^en([-_]|$)/i.test(v.lang)).sort((a, b) => score(b) - score(a) || a.name.localeCompare(b.name));
  voice = voices.find(v => v.name === voiceName) || voices[0] || null;
  listeners.voices.forEach(f => f(voices));
}
const listeners = {voices: [], caption: [], state: [], live: []};
if (synth) { loadVoices(); if (synth.addEventListener) synth.addEventListener('voiceschanged', loadVoices); else synth.onvoiceschanged = loadVoices; }

let session = 0, speaking = false, unlocked = false, current = null;   // current: the utterance being read, held so its end event arrives
function speakOne(text, rate) {
  return new Promise(resolve => {
    if (!synth || !voices.length) return setTimeout(() => resolve(true), Math.max(1200, text.split(' ').length * 330 / rate));   // no voice: the words are shown for as long as reading them would take
    const u = new SpeechSynthesisUtterance(text);
    if (voice) { u.voice = voice; u.lang = voice.lang; } else u.lang = 'en-US';
    u.rate = rate; u.pitch = 1; u.volume = volume;
    let done = false; current = u;
    const finish = ok => { if (done) return; done = true; clearTimeout(watch); if (current === u) current = null; resolve(ok); };
    // Stopped on purpose: at once. Not allowed yet (no touch so far) or failed: the words stay up for their reading time.
    u.onend = () => finish(true);
    u.onerror = e => ['interrupted', 'canceled'].includes(e.error) ? finish(false) : setTimeout(() => finish(true), Math.max(1200, text.split(' ').length * 330 / rate));
    const watch = setTimeout(() => finish(true), 2000 + 1.6 * text.length / (14 * rate) * 1000);   // some browsers never report the end
    synth.speak(u);
  });
}

// ---- Sounds: made in the browser. A quiet radio bed, a sound for the town, and short cues ----
let ctx = null, master = null, bed = null, townBus = null, townBed = null, noise = {};
// The context asks for steady playback (bigger buffers) rather than the smallest delay: nothing here needs a fast
// response, and small buffers crackle when the computer is busy. A limiter is the last step, so voices together never clip.
function audio() {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return null;
    try { ctx = new AC({latencyHint: 'playback'}); } catch { ctx = new AC(); }
    master = ctx.createGain(); master.gain.value = volume;
    const limit = ctx.createDynamicsCompressor(); limit.threshold.value = -3; limit.knee.value = 0; limit.ratio.value = 20; limit.attack.value = .003; limit.release.value = .25;
    master.connect(limit).connect(ctx.destination);
    // A hidden page goes quiet and lets the sound card rest; it comes back when the page does.
    document.addEventListener('visibilitychange', () => {
      if (!ctx) return;
      if (document.hidden) { master.gain.setTargetAtTime(0, ctx.currentTime, .08); setTimeout(() => { if (document.hidden && ctx.state === 'running') ctx.suspend().catch(() => {}); }, 400); }
      else ctx.resume().then(() => master.gain.setTargetAtTime(volume, ctx.currentTime, .1)).catch(() => {});
    });
  }
  if (ctx.state === 'suspended' && !document.hidden) ctx.resume().catch(() => {});
  return ctx;
}
// Waits (briefly) for the context to run: resume() is asynchronous, so right after a touch the state can still say "suspended".
function ready(ms = 1500) {
  if (!audio()) return Promise.resolve(false);
  if (ctx.state === 'running') return Promise.resolve(true);
  return Promise.race([ctx.resume().then(() => ctx.state === 'running', () => false), wait(ms).then(() => ctx.state === 'running')]);
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
  const hiss = source('white'); hiss.connect(filter('bandpass', 2600, .6)).connect(gain(.006)).connect(bed); hiss.start();
  bed.gain.setTargetAtTime(1, ctx.currentTime, .5);
  townBus = gain(1); townBus.connect(master);
}
function stopBed() {
  for (const g of [bed, townBus]) if (g) { g.gain.setTargetAtTime(0, ctx.currentTime, .25); const old = g; setTimeout(() => old.disconnect(), 1500); }
  bed = townBus = townBed = null;
}
// Which sounds suit a town: a harbour, a busy street or the country. New York keeps its siren.
const SEA = /^(Portland|Portsmouth|Newburyport|Salem|Boston|Providence|Warren|Newport|New York|Philadelphia|Wilmington|Alexandria|Norfolk|Charleston|Baltimore)$/;
const STREET = /^(Boston|New York|Philadelphia|Charleston|Washington|Richmond|Baltimore|Hartford|Lexington)$/;
function scheme(name) {
  if (name === 'New York') return {bed: 'traffic', cue: 'siren'};   // the deliberate anachronism: a modern city morning
  return {bed: SEA.test(name) ? 'sea' : STREET.test(name) ? 'city' : 'country', cue: STREET.test(name) ? 'hooves' : SEA.test(name) ? 'ship' : 'birds'};
}
// The bed changes at most once in 2.5 seconds: a quick sweep across towns leaves it alone, and the last town wins.
let bedAt = -1e9, bedTimer = 0;
function setTownBed(kind) {
  if (!ctx || !townBus) return;
  clearTimeout(bedTimer); if (townBed?.kind === kind) return;
  const since = performance.now() - bedAt;
  if (townBed && since < 2500) { bedTimer = setTimeout(() => setTownBed(kind), 2500 - since); return; }
  bedAt = performance.now();
  if (townBed) { const old = townBed; old.g.gain.setTargetAtTime(0, ctx.currentTime, .6); setTimeout(() => { old.stop(); old.g.disconnect(); }, 3000); }
  const g = gain(0), stops = [];
  if (kind === 'sea') {   // water against a wharf: low noise that swells and falls
    const s = source('brown'), f = filter('lowpass', 520), swell = gain(.5), lfo = ctx.createOscillator(), depth = gain(.45);
    lfo.frequency.value = .11; lfo.connect(depth).connect(swell.gain); s.connect(f).connect(swell).connect(g); s.start(); lfo.start(); stops.push(s, lfo);
  } else if (kind === 'traffic') {   // New York: the faint hum of city traffic, with a car passing now and then (with the siren, on purpose)
    const s = source('brown'), f = filter('lowpass', 200); s.connect(f).connect(gain(.85)).connect(g); s.start(); stops.push(s);   // the low rumble
    const hiss = source('white'), hf = filter('bandpass', 1500, .5); hiss.connect(hf).connect(gain(.035)).connect(g); hiss.start(); stops.push(hiss);   // tyres, far off
    const pass = () => {   // a car going by: a swell of noise that moves from one side to the other
      if (!ctx || !townBed || townBed.kind !== 'traffic' || ctx.state !== 'running') return;
      const t = ctx.currentTime, dur = 3 + Math.random() * 3, n = source('brown'), bp = filter('bandpass', 320 + Math.random() * 320, .9), cg = gain(0);
      const pn = ctx.createStereoPanner ? ctx.createStereoPanner() : null, dir = Math.random() < .5 ? 1 : -1;
      n.connect(bp).connect(cg); (pn ? cg.connect(pn) : cg).connect(g);
      cg.gain.setValueAtTime(0, t); cg.gain.linearRampToValueAtTime(.45 + Math.random() * .4, t + dur * .5); cg.gain.linearRampToValueAtTime(0, t + dur);
      if (pn) { pn.pan.setValueAtTime(-.85 * dir, t); pn.pan.linearRampToValueAtTime(.85 * dir, t + dur); }
      n.start(t); n.stop(t + dur + .05);
    };
    const timer = setInterval(() => { if (Math.random() < .5) pass(); }, 2300); setTimeout(pass, 400);
    stops.push({stop: () => clearInterval(timer)});
  } else if (kind === 'city') {   // the murmur of a street
    const s = source('brown'), f = filter('lowpass', 300); s.connect(f).connect(gain(.8)).connect(g); s.start(); stops.push(s);
  } else {   // the country: a faint air
    const s = source('brown'), f = filter('lowpass', 180); s.connect(f).connect(gain(.35)).connect(g); s.start(); stops.push(s);
  }
  g.connect(townBus); g.gain.setTargetAtTime(.09, ctx.currentTime, .8);
  townBed = {kind, g, stop: () => stops.forEach(s => { try { s.stop(); } catch {} })};
}
function duck(on) { if (townBus && ctx) townBus.gain.setTargetAtTime(on ? .45 : 1, ctx.currentTime, .3); }
// A street between tall buildings: a few early echoes off the facades (different left and right), then a long tail that
// grows darker as it fades. Made once; each town sound borrows it for as long as it rings.
let streetIR = null;
function streetImpulse(c, seconds = 3.4) {
  const rate = c.sampleRate, len = Math.round(rate * seconds), b = c.createBuffer(2, len, rate);
  for (let ch = 0; ch < 2; ch++) {
    const d = b.getChannelData(ch); let lp = 0;
    for (let i = 0; i < len; i++) {
      const t = i / rate, bright = .5 - .44 * Math.min(1, t / 2.2);
      lp += (Math.random() * 2 - 1 - lp) * bright;
      d[i] = lp * Math.exp(-t * 1.25) * Math.min(1, t / .03) * .9;
    }
    for (const [ms, a] of (ch ? [[63, .55], [131, .42], [217, .32], [349, .22], [503, .14]] : [[47, .6], [109, .45], [188, .34], [301, .24], [457, .15]])) {
      const at = Math.round(ms / 1000 * rate);
      for (let k = 0; k < 160 && at + k < len; k++) d[at + k] += (Math.random() * 2 - 1) * a * Math.pow(1 - k / 160, 2);
    }
  }
  return b;
}
function echo(from, amount, ms) {   // send a town sound into the street, then let the echo go when it has died away
  const rev = ctx.createConvolver(); rev.buffer = streetIR || (streetIR = streetImpulse(ctx));
  const send = gain(amount), back = filter('highpass', 150), dest = townBus || master;
  from.connect(send); send.connect(rev).connect(back).connect(dest);
  setTimeout(() => { for (const n of [send, rev, back]) try { n.disconnect(); } catch {} }, ms + 4200);
}
// How much each town sound echoes, and how long it rings (ms) in its long and short forms: the siren most, a city's
// sound a few streets away. The long forms open the radio and each item of the Radio page; the short ones (about a
// second) sit under a voice on Pulses and the telescope.
let sirenAt = -1e9;
const SPACE = {siren: [1.25, 12500, 4200], church: [.75, 9200, 4500], ship: [.55, 5200, 2200], hooves: [.5, 6400, 2200], drum: [.4, 4300, 1300], birds: [.18, 6800, 1500]};
// Bell-like tones from inharmonic partials.
function bell(at, base, ratios, decay, level, out) {
  for (const [k, r] of ratios.entries()) {
    const o = ctx.createOscillator(), g = gain(0); o.frequency.value = base * r; o.connect(g).connect(out);
    g.gain.setValueAtTime(0, at); g.gain.linearRampToValueAtTime(level / (k + 1.2), at + .006); g.gain.exponentialRampToValueAtTime(.0001, at + decay * (1.2 - k * .08));
    o.start(at); o.stop(at + decay * 1.3);
  }
}
function cue(kind, short = false) {
  if (!ctx) return 0;
  if (ctx.state !== 'running') {
    const asked = performance.now();
    ctx.resume().then(() => { if (ctx.state === 'running' && performance.now() - asked < 1500) cue(kind, short); }).catch(() => {});
    return 0;
  }
  if (kind === 'siren' && performance.now() - sirenAt < 45000) return 0;   // not again for a while: once in 45 seconds is a city, more is an alarm
  const t = ctx.currentTime + .05, far = filter('lowpass', 2600); far.connect(townBus || master);
  const pan = ctx.createStereoPanner ? ctx.createStereoPanner() : null, out = pan ? (pan.connect(far), pan) : far;
  if (SPACE[kind]) echo(far, SPACE[kind][0], SPACE[kind][short ? 2 : 1]);
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
  if (kind === 'church') { for (let i = 0; i < (short ? 1 : 4); i++) bell(t + i * 2.1, 196, [.5, 1, 1.183, 1.506, 2, 2.514, 2.662], short ? 3 : 4, .07, out); return short ? 400 : 1200; }
  if (kind === 'ship') { for (const k of short ? [0, .38] : [0, .38, 1.4, 1.78, 2.8, 3.18]) bell(t + k, 1046, [1, 2.0, 2.76, 5.4], 1.4, .05, out); return short ? 300 : 600; }
  if (kind === 'siren') {   // a siren a few streets away: its wail passes across the city and rings between the buildings
    sirenAt = performance.now();
    const wails = short ? 1 : 4, dur = wails * 3, f = filter('lowpass', 1700), g = gain(0);
    for (const [type, mul, lvl] of [['sawtooth', 1, .62], ['triangle', 2.004, .22]]) {
      const o = ctx.createOscillator(), og = gain(lvl), base = 610 * mul; o.type = type;
      o.frequency.setValueAtTime(base, t);
      for (let k = 0; k < wails; k++) { o.frequency.linearRampToValueAtTime(base * 1.95, t + k * 3 + 1.5); o.frequency.linearRampToValueAtTime(base, t + k * 3 + 3); }
      o.detune.setValueAtTime(35, t); o.detune.linearRampToValueAtTime(-70, t + dur);   // passing by: a little lower as it goes away
      o.connect(og).connect(f); o.start(t); o.stop(t + dur);
    }
    f.connect(g).connect(out);
    g.gain.setValueAtTime(0, t);
    if (short) { g.gain.linearRampToValueAtTime(.011, t + 1); g.gain.linearRampToValueAtTime(0, t + dur - .2); }
    else { g.gain.linearRampToValueAtTime(.012, t + 2.2); g.gain.linearRampToValueAtTime(.017, t + 6.5); g.gain.linearRampToValueAtTime(0, t + dur - .3); }
    if (pan) { pan.pan.setValueAtTime(short ? -.4 : -.8, t); pan.pan.linearRampToValueAtTime(short ? .3 : .7, t + dur); }
    return 700;
  }
  if (kind === 'hooves') {   // a horse and cart passing
    const g = gain(0), len = short ? 1.5 : 6; g.connect(out);
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.9, t + len * .35); g.gain.linearRampToValueAtTime(0, t + len);
    if (pan) { pan.pan.setValueAtTime(short ? .4 : .8, t); pan.pan.linearRampToValueAtTime(short ? -.3 : -.8, t + len); }
    for (let k = 0, at = t; at < t + len; k++) {
      const s = source('click', false), f = filter('bandpass', 700 + 300 * (k % 2), 2), o = ctx.createOscillator(), og = gain(0);
      s.connect(f).connect(gain(.5)).connect(g); s.start(at);
      o.frequency.value = 180 + 60 * (k % 2); o.connect(og).connect(g); og.gain.setValueAtTime(.12, at); og.gain.exponentialRampToValueAtTime(.0001, at + .07); o.start(at); o.stop(at + .08);
      at += k % 2 ? .23 : .13;
    }
    return 500;
  }
  if (kind === 'birds') {   // morning birds
    for (let n = 0; n < (short ? 1 : 5); n++) {
      const at0 = t + n * 1.3 + Math.random() * .5, base = 2600 + Math.random() * 1600;
      for (let k = 0; k < 3; k++) {
        const o = ctx.createOscillator(), g = gain(0), at = at0 + k * .14; o.frequency.setValueAtTime(base, at); o.frequency.exponentialRampToValueAtTime(base * 1.5, at + .07);
        o.connect(g).connect(out); g.gain.setValueAtTime(0, at); g.gain.linearRampToValueAtTime(.025, at + .02); g.gain.linearRampToValueAtTime(0, at + .09); o.start(at); o.stop(at + .1);
      }
    }
    return 500;
  }
  if (kind === 'drum') {   // a distant drum, under war news
    const pattern = short ? [0, .18, .36] : [0, .18, .36, .9, 1.08, 1.26, 1.8, 2.25, 2.7, 2.88, 3.06, 3.6];
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
let saySrc = null;   // the recording being read on the Radio page, so stop() can end it
function playRecorded(buf, live_) {
  return new Promise(resolve => {
    const c = audio(), src = c.createBufferSource(), g = gain(.85); src.buffer = buf; src.connect(g).connect(clearOut(c));
    const t = c.currentTime; src.playbackRate.setValueAtTime(.6, t); src.playbackRate.exponentialRampToValueAtTime(1, t + .2);
    saySrc = {src, g}; let done = false;
    const finish = ok => { if (done) return; done = true; clearInterval(watch); if (saySrc && saySrc.src === src) saySrc = null; resolve(ok); };
    const watch = setInterval(() => { if (!live_()) { try { g.gain.setTargetAtTime(0, c.currentTime, .08); src.stop(c.currentTime + .3); } catch {} finish(false); } }, 150);
    src.onended = () => finish(live_()); src.start(t);
  });
}
async function sayRecorded(item, {greet = false, previous = null, chime = false} = {}) {
  if (!item.clip || !(await ready(800))) return null;
  await loadClips(); if (!hasClip(item.clip)) return null;
  const my = ++session, busy = synth && (synth.speaking || synth.pending); if (synth) synth.cancel();
  const live_ = () => my === session;
  if (busy) await wait(60);
  startBed();
  const name = town(item.place), sc = scheme(name), head = intro(item, greet, previous);
  const lines = chunks(clean(item.text || item.title));
  const show = index => listeners.caption.forEach(f => f({item, intro: head.lines.join(' '), lines, index}));
  speaking = true; listeners.state.forEach(f => f('speaking'));
  try {
    show(-1);
    if (chime) await wait(cue('chime')); else if (!greet && live_()) await wait(cue('tune'));
    if (!live_()) return false;
    if (greet) cue('church');
    setTownBed(sc.bed); duck(true);
    const {y, m, d, wd} = parts(item.date), sameDay = previous && previous.date === item.date;
    const date = [`a:day:${d}`, `a:month:${m}`, `a:year:${y}`], paper = item.lccn ? [`a:paper:${item.lccn}`] : [];
    const ids = greet ? [`a:hello:${name}`, `a:weekday:${DAYS[wd]}`, ...date, ...paper] : sameDay ? paper : [...date, ...paper];
    cue(item.war ? 'drum' : sc.cue);
    const head_ = await joinClips(ids.filter(hasClip));
    if (head_ && live_()) await playRecorded(head_.buf, live_);
    if (!live_()) return false;
    await wait(250);
    const body = await joinClips([item.clip]); if (!body) return null;
    // The captions follow the reading: each sentence shown for its share of the recording, by its length.
    const total = lines.reduce((n, l) => n + l.length, 0) || 1; let at = 0;
    const timers = lines.map((l, i) => { const ms = at / total * body.buf.duration * 1000; at += l.length; return setTimeout(() => { if (live_()) show(i); }, ms); });
    const ok = await playRecorded(body.buf, live_); timers.forEach(clearTimeout);
    if (!ok || !live_()) return false;
    duck(false); await wait(700);
    return live_();
  } finally {
    if (live_()) { speaking = false; listeners.state.forEach(f => f('idle')); }
  }
}
async function say(item, opts = {}) {
  if (item.clip && opts.mode !== 'title' && opts.mode !== 'intro') { const r = await sayRecorded(item, opts); if (r !== null) return r; }   // no recording: the browser's voice
  return sayAloud(item, opts);
}
async function sayAloud(item, {greet = false, previous = null, rate = 1, mode = 'full', chime = false} = {}) {
  const my = ++session, busy = synth && (synth.speaking || synth.pending); if (synth) synth.cancel();
  const pace = () => typeof rate === 'function' ? rate() : rate;
  const live = () => my === session;
  if (busy) await wait(60);
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
  const my = ++session, busy = synth && (synth.speaking || synth.pending); if (synth) synth.cancel();
  const live = () => my === session, lines = chunks(clean(text));
  if (busy) await wait(60);
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
  if (saySrc && ctx) { try { saySrc.g.gain.setTargetAtTime(0, ctx.currentTime, .06); saySrc.src.stop(ctx.currentTime + .25); } catch {} saySrc = null; }
  if (silence) { liveStopAll({scratch: false}); stopBed(); }
  listeners.state.forEach(f => f(silence ? 'off' : 'idle'));
}

// ---- Voices on demand: Pulses and the telescope ----
// On these pages the radio plays recordings only (see "Recorded voices" below). A star or a paper speaks when the
// visitor points at it, clicks it or selects an area, and on its own while the radio is on and nobody is at the
// controls (the pages choose what, and ask for a long or a short opening with `lead`). A story with no recording gets
// the announcer's recorded introduction (its town or paper and its date) while its words stay on air. Several voices
// can speak at once (up to five), each placed left or right by where its story is on the screen. Moving on to another
// star stops the old voice the way a hand stops a record (it slows, drops and fades, with a scratch) and spins the new
// one up. The atmosphere comes in three layers, so quick switching still reaches the news at once: the town's bed runs
// all the time and changes only when another kind of town has spoken (setTownBed); a town's own sound, about a second
// long, starts under a voice that has been heard for half a second, at most once in eight seconds (cueSoft); and the
// long opening (bells, the town's sound, then the greeting) comes only when the radio is turned on, with a short one
// (the tuning sound, then the place and date) before each story a page plays on its own.
const LIVE_MAX = 5;
let liveBus = null, scratchAt = 0;
const live = new Map();     // key -> {src, g, label, text, ending, silent, recorded}
const liveChanged = () => {
  const on = [...live.entries()].filter(([, v]) => !v.ending);
  duck(on.some(([, v]) => v.src));   // the town's bed steps back while anyone speaks
  listeners.live.forEach(f => f(on.map(([key, v]) => ({key, label: v.label, text: v.text, silent: !!v.silent, recorded: !!v.recorded}))));
};
function roomImpulse(c) {   // a small room: six tenths of a second of decaying noise
  const len = Math.round(c.sampleRate * .6), b = c.createBuffer(2, len, c.sampleRate);
  for (let ch = 0; ch < 2; ch++) { const d = b.getChannelData(ch); for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3.4); }
  return b;
}
function liveOut(c) {
  if (liveBus) return liveBus;
  liveBus = gain(1);
  const band = filter('lowpass', 4200); liveBus.connect(filter('highpass', 220)).connect(band).connect(master);
  const room = c.createConvolver(); room.buffer = roomImpulse(c); band.connect(room).connect(gain(.12)).connect(master);
  return liveBus;
}
// A town's own sound under a voice: the short form, and rare enough that a quick sweep across the sky hears none.
let softAt = -1e9; const softKind = {};
function cueSoft(kind) {
  const now = performance.now();
  if (!kind || now - softAt < 8000 || now - (softKind[kind] || -1e9) < 20000) return;
  softAt = softKind[kind] = now; cue(kind, true);
}
// key: who speaks ('star:12', 'paper:sn123'); text: the words for the caption; clips: the recording (announcer lines,
// then the story's own); host: the announcer's lines alone, for a story with no recording; label, and words (a longer
// caption for a story with no recording): what shows on air; town: for the bed and the town's sound; war: a drum
// instead; lead: 'full' (the radio was just turned on), 'short' (a story the page plays on its own) or none (the visitor
// asked: the voice starts at once); cut: seconds after which the voice fades (0: to the end).
// Resolves to true when the voice was heard to the end.
async function livePlay(key, text, {pan = 0, level = .5, label = '', words = '', spin = true, clips = null, host = null, cut = 0, town = '', war = false, lead = ''} = {}) {
  const c = audio(); if (!c || (!text && !clips && !host)) return false;
  const now = live.get(key); if (now && !now.ending) return true;   // already speaking
  const speaking = [...live.entries()].filter(([, v]) => !v.ending);
  if (speaking.length >= LIVE_MAX) liveStop(speaking[0][0]);   // the oldest gives way
  const entry = {src: null, g: null, label, text: clean(text), ending: false, silent: false, recorded: false};
  live.set(key, entry); liveChanged();
  const gone = () => live.get(key) !== entry || entry.ending;
  const hold = async () => {   // the words stay on air for their reading time (or until stopped)
    const end = performance.now() + Math.max(2500, entry.text.split(' ').length * 330);
    while (!gone() && performance.now() < end) await wait(150);
  };
  try {
    if (!(await ready()) || gone()) return false;
    startBed();
    const sc = scheme(town), own = war ? 'drum' : sc.cue;
    const asked = clips && clips.length ? joinClips(clips) : Promise.resolve(null);   // fetched while an opening plays
    if (lead === 'short') { await wait(cue('tune')); if (gone()) return false; }
    let rec = await asked, wordsOnly = false; if (gone()) return false;
    if (!rec && host && host.length) { rec = await joinClips(host); wordsOnly = !!rec; if (gone()) return false; }
    if (town) setTownBed(sc.bed);
    if (lead === 'full') {   // the radio has just been turned on: church bells, the town's own sound, then the greeting
      cue('church'); setTimeout(() => { if (!gone()) cue(own); }, 900);
      await wait(1600); if (gone()) return false;
    }
    if (!rec || wordsOnly) { entry.label = words || label; entry.silent = !rec; liveChanged(); }
    if (!rec) { await hold(); return false; }
    entry.recorded = !wordsOnly;
    // Several voices together: each a little quieter (3 dB for every other voice), so the sum stays below the limiter.
    const together = [...live.values()].filter(v => !v.ending && v.src).length, lvl = level * Math.pow(10, -3 * together / 20);
    const src = c.createBufferSource(), g = gain(0), pn = c.createStereoPanner ? c.createStereoPanner() : null, t = c.currentTime;
    src.buffer = rec.buf;
    if (spin) { src.playbackRate.setValueAtTime(.55, t); src.playbackRate.exponentialRampToValueAtTime(1, t + .22); }   // spun up, like a record let go
    const bus = rec.tier <= 1 ? clearOut(c) : liveOut(c);
    if (pn) { pn.pan.value = Math.max(-1, Math.min(1, pan)); src.connect(g).connect(pn).connect(bus); } else src.connect(g).connect(bus);
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(lvl, t + .08);
    entry.src = src; entry.g = g; liveChanged();
    if (lead !== 'full') setTimeout(() => { if (!gone()) cueSoft(own); }, 500);
    // A hover hears the opening only: after `cut` seconds the voice fades away (no scratch), as a station drifts off.
    if (cut > 0 && rec.buf.duration > cut + 1.5) setTimeout(() => { if (live.get(key) === entry && !entry.ending) liveFade(key); }, cut * 1000);
    const heard = await new Promise(resolve => { src.onended = () => resolve(!entry.ending); src.start(t); });
    if (heard && wordsOnly && !gone()) { entry.src = null; liveChanged(); await hold(); }
    return heard;
  } catch { return false; }
  finally { if (live.get(key) === entry) { live.delete(key); liveChanged(); } }
}
// ---- Recorded voices: speech made once at build time with Kokoro (work/audio_render.py) ----
// audio/index.json lists every clip: [pack, first byte, end byte, seconds, tier] (tier 0 the announcer, 1 a reviewed
// passage, 2 a title of a widely printed story), plus aliases (a reviewed story -> its first printing). Each clip is a
// whole MP3 inside its pack, so a byte range of the pack plays alone. If the server ignores ranges, the whole pack is
// fetched once and cut here.
let clipIndex = null, clipLoading = null;
const clipCache = new Map(), wholePacks = new Map();
function loadClips() {
  if (clipIndex) return Promise.resolve(clipIndex);
  return clipLoading = clipLoading || fetch(new URL('audio/index.json', document.baseURI)).then(r => r.ok ? r.json() : null).catch(() => null).then(j => (clipIndex = j));
}
const clipId = id => clipIndex && clipIndex.alias && clipIndex.alias[id] || id;
const hasClip = id => !!(clipIndex && clipIndex.clips[clipId(id)]);
async function clipBuffer(id) {
  const c = audio(); await loadClips(); id = clipId(id);
  const e = c && clipIndex && clipIndex.clips[id]; if (!e) return null;
  if (clipCache.has(id)) { const b = clipCache.get(id); clipCache.delete(id); clipCache.set(id, b); return b; }
  const url = new URL('audio/' + clipIndex.packs[e[0]], document.baseURI).href;
  let bytes = null;
  try {
    if (wholePacks.has(url)) bytes = (await wholePacks.get(url)).slice(e[1], e[2]);
    else {
      const r = await fetch(url, {headers: {Range: `bytes=${e[1]}-${e[2] - 1}`}});
      if (r.status === 206) bytes = await r.arrayBuffer();
      else if (r.ok) { const whole = r.arrayBuffer(); wholePacks.set(url, whole); bytes = (await whole).slice(e[1], e[2]); }
    }
    if (!bytes) return null;
    const buf = await c.decodeAudioData(bytes);
    clipCache.set(id, buf); if (clipCache.size > 80) clipCache.delete(clipCache.keys().next().value);
    return buf;
  } catch { return null; }
}
// Several clips as one: the announcer's words with short breaths between them, then a longer pause before the reader.
// Two announcers take turns, a man (am_michael, 'a:' clips) and a woman (af_heart, 'b:' clips): each introduction is
// said whole by one of them, and the next introduction goes to the other. Pages ask for 'a:' clips; the host is chosen here.
let hostTurn = 0;
async function joinClips(ids) {
  await loadClips(); if (!ids.length) return null;
  if (ids.some(id => id.startsWith('a:'))) {
    const host = ['a:', 'b:'][hostTurn++ % 2], cast = ids.map(id => id.startsWith('a:') ? host + id.slice(2) : id);
    if (cast.every(hasClip)) ids = cast;   // that host has every line; otherwise the first host speaks
  }
  ids = ids.filter(id => hasClip(id) || !/^[ab]:/.test(id));   // an announcer's line that was never recorded is left out
  if (!ids.length || !ids.every(hasClip)) return null;
  const bufs = await Promise.all(ids.map(clipBuffer)); if (bufs.some(b => !b)) return null;
  if (bufs.length === 1) return {buf: bufs[0], tier: clipIndex.clips[clipId(ids[0])][4]};
  const rate = bufs[0].sampleRate, gaps = ids.map((id, k) => k === ids.length - 1 ? 0 : clipIndex.clips[clipId(ids[k + 1])][4] > 0 ? .4 : .1);
  const len = bufs.reduce((n, b, k) => n + b.length + Math.round(gaps[k] * rate), 0), out = ctx.createBuffer(1, len, rate), d = out.getChannelData(0);
  let at = 0; bufs.forEach((b, k) => { d.set(b.getChannelData(0), at); at += b.length + Math.round(gaps[k] * rate); });
  return {buf: out, tier: Math.max(...ids.map(id => clipIndex.clips[clipId(id)][4]))};
}
// A clear station (the announcer, a reviewed passage): the full voice in a light room. Titles go through the
// radio band (liveOut) instead, as distant stations.
let clearBus = null;
function clearOut(c) {
  if (clearBus) return clearBus;
  clearBus = gain(1); const lo = filter('highpass', 90); clearBus.connect(lo).connect(master);
  const room = c.createConvolver(); room.buffer = roomImpulse(c); lo.connect(room).connect(gain(.07)).connect(master);
  return clearBus;
}

// Stopping a voice: like a hand on a record, it slows, drops in pitch and fades, with a scratch.
function liveStop(key, {scratch = true} = {}) {
  const e = live.get(key); if (!e || e.ending) return;
  e.ending = true; liveChanged();
  if (!e.src) { live.delete(key); liveChanged(); return; }   // still being made (or only a caption): it never starts
  const t = ctx.currentTime;
  try {
    e.src.playbackRate.cancelScheduledValues(t); e.src.playbackRate.setValueAtTime(Math.max(.2, e.src.playbackRate.value), t); e.src.playbackRate.exponentialRampToValueAtTime(.16, t + .34);
    e.g.gain.cancelScheduledValues(t); e.g.gain.setValueAtTime(e.g.gain.value, t); e.g.gain.linearRampToValueAtTime(0, t + .36);
    e.src.stop(t + .4);
  } catch {}
  if (scratch && performance.now() - scratchAt > 140) { scratchAt = performance.now(); cue('scratch'); }   // one scratch for several stopped together
}
function liveStopAll(opts) { for (const k of [...live.keys()]) liveStop(k, opts); }
function liveFade(key) {   // a gentle end: the voice fades over most of a second, at its own pitch
  const e = live.get(key); if (!e || e.ending || !e.src) return;
  e.ending = true; liveChanged();
  const t = ctx.currentTime; try { e.g.gain.cancelScheduledValues(t); e.g.gain.setValueAtTime(e.g.gain.value, t); e.g.gain.linearRampToValueAtTime(0, t + .8); e.src.stop(t + .85); } catch {}
}
const firstWords = (text, n) => {
  const w = clean(text).split(' ').filter(Boolean); if (w.length <= n) return w.join(' ');
  let cut = n; for (let k = n; k >= Math.ceil(n * .6); k--) if (/[,.;:!?]$/.test(w[k - 1])) { cut = k; break; }
  return w.slice(0, cut).join(' ').replace(/[,;:]$/, '') + '…';
};
// The opening of the radio: the strings once a visit (per tab), a short tuning sound after that.
function welcome() {
  let first = true; try { first = !sessionStorage.getItem('nns-strings'); sessionStorage.setItem('nns-strings', '1'); } catch {}
  return cue(first ? 'strings' : 'tune');
}
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
  say, sayLine, stop, unlock, ready, cue: (k, short) => { audio(); return cue(k, short); }, welcome: () => { audio(); return welcome(); },
  live: {
    play: livePlay, stop: liveStop, stopAll: liveStopAll, has: key => !!live.get(key) && !live.get(key).ending,
    preload: () => { loadClips(); audio(); },
    get count() { return [...live.values()].filter(v => !v.ending).length; },
    fade: liveFade, clips: {load: loadClips, has: hasClip, id: clipId},
    onChange(f) { listeners.live.push(f); }, firstWords, MAX: LIVE_MAX
  },
  spokenDate, writtenDate, town, paperName, clean, chunks, intro
};
})();
