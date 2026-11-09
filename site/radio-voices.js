/* Newspaper Night Sky · the chorus voices, a module worker started by radio.js.
   eSpeak (meSpeak 2.0.2, GPL-3.0, loaded from jsdelivr) turns short texts into speech here, away from the page, so the
   map and the stars keep moving. It only starts when the radio's chorus is first used, and nothing is sent anywhere:
   the text goes in, a WAV file comes out, all inside the visitor's browser.
   Message in: {id, text, opts: {speed (words per minute), variant, pitch}}. Message out: {id, buf (WAV)} or {id, error}. */
const BASE = 'https://cdn.jsdelivr.net/npm/mespeak@2.0.2/';
let me = null, loading = null;
async function load() {
  const mod = await import(BASE + '+esm'); me = mod.default || mod;
  const [config, voice] = await Promise.all(['src/mespeak_config.json', 'voices/en/en-us.json'].map(f => fetch(BASE + f).then(r => r.json())));
  me.loadConfig(config); me.loadVoice(voice);
}
function render(text, opts) {
  let out;
  try { out = me.speak(text, {...opts, rawdata: 'buffer'}); } catch { out = null; }
  if (!out) out = me.speak(text, {speed: opts.speed, pitch: opts.pitch, rawdata: 'buffer'});   // a variant it does not know: the plain voice
  return out instanceof ArrayBuffer ? out : new Uint8Array(out).buffer;
}
self.onmessage = async e => {
  const {id, text, opts} = e.data;
  try {
    await (loading = loading || load());
    const buf = render(text, opts || {});
    self.postMessage({id, buf}, [buf]);
  } catch (err) {
    loading = null;
    self.postMessage({id, error: String(err)});
  }
};
