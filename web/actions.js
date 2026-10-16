// SafeShelf judges' page, part 2: what a shopper can do with an answer.
//   - Listen: the verdict read aloud in 26 JAPAC languages (POST /v1/voice/verdict), short enough for a shop aisle
//   - "Checked by code, not guessed" badges on each country line, linked to the official record
//   - I already bought it: steps, refund request and regulator complaint drafts, case file (POST /v1/after-purchase),
//     and an incident report with a photo (POST /v1/incidents)
//   - Ask out loud: camera + voice with Gemini Live (WebSocket /v1/live); falls back to a photo + spoken question
//     (POST /v1/camera/ask). Works without reading the screen.
//   - Attacker vs defender: the evidence red-team replayed, and live rounds where Gemini invents the attack
// Plain module, no build step. Text is always set as text, never as HTML.
const DEFAULT_API = "https://safeshelf-api-368488022657.asia-south1.run.app";
// ?api=http://localhost:8080 points the page at a local API (localhost only).
const override = new URLSearchParams(location.search).get("api");
export const API = override && /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(override) ? override : DEFAULT_API;

export const el = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k.includes("-") || k === "role" || k === "for") e.setAttribute(k, v);
    else e[k] = v;
  }
  e.append(...kids.filter((k) => k !== null && k !== undefined && k !== false));
  return e;
};

// [code the API takes, name in its own script, speech locale] (same codes as engine/chat_core.py LANGUAGES)
export const LANGS = [["en", "English", "en-IN"], ["hi", "हिन्दी", "hi-IN"], ["bn", "বাংলা", "bn-IN"], ["mr", "मराठी", "mr-IN"],
  ["te", "తెలుగు", "te-IN"], ["ta", "தமிழ்", "ta-IN"], ["gu", "ગુજરાતી", "gu-IN"], ["ur", "اردو", "ur-IN"], ["kn", "ಕನ್ನಡ", "kn-IN"],
  ["or", "ଓଡ଼ିଆ", "or-IN"], ["ml", "മലയാളം", "ml-IN"], ["pa", "ਪੰਜਾਬੀ", "pa-IN"], ["ne", "नेपाली", "ne-NP"], ["si", "සිංහල", "si-LK"],
  ["ja", "日本語", "ja-JP"], ["ko", "한국어", "ko-KR"], ["zh-Hans", "简体中文", "zh-CN"], ["zh-Hant", "繁體中文", "zh-TW"],
  ["id", "Bahasa Indonesia", "id-ID"], ["ms", "Bahasa Melayu", "ms-MY"], ["th", "ไทย", "th-TH"], ["vi", "Tiếng Việt", "vi-VN"],
  ["fil", "Filipino", "fil-PH"], ["my", "မြန်မာ", "my-MM"], ["km", "ខ្មែរ", "km-KH"], ["lo", "ລາວ", "lo-LA"]];
const LANG_KEY = "safeshelf-lang";
const savedLang = () => {
  try { const v = localStorage.getItem(LANG_KEY); if (v && LANGS.some(([c]) => c === v)) return v; } catch (_) { /* no storage */ }
  const nav = (navigator.language || "en").toLowerCase();
  return (LANGS.find(([c]) => nav.startsWith(c.toLowerCase())) || LANGS[0])[0];
};
export function langSelect(label = "Language") {
  const s = el("select", { "aria-label": label }, ...LANGS.map(([c, n]) => { const o = el("option", { value: c, textContent: n }); o.lang = c; return o; }));
  s.value = savedLang();
  s.onchange = () => { try { localStorage.setItem(LANG_KEY, s.value); } catch (_) { /* no storage */ } };
  return s;
}

// Speak with the device's voice for that language; say so when the device has none (an English voice would read nonsense).
export function speak(text, locale, onNoVoice) {
  if (!("speechSynthesis" in window) || !text) return false;
  speechSynthesis.cancel();
  const base = locale.split("-")[0].toLowerCase();
  const voices = speechSynthesis.getVoices();
  const voice = voices.find((v) => v.lang.replace("_", "-").toLowerCase() === locale.toLowerCase())
    || voices.find((v) => v.lang.toLowerCase().startsWith(base));
  if (!voice && base !== "en" && voices.length) { onNoVoice?.(); return false; }
  const u = new SpeechSynthesisUtterance(text);
  u.lang = locale;
  if (voice) u.voice = voice;
  u.rate = 0.95;
  speechSynthesis.speak(u);
  return true;
}

async function post(path, body, timeout = 120000) {
  const res = await fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: AbortSignal.timeout(timeout) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `the API answered ${res.status}`);
  return data;
}

// --- Listen: the verdict, short, in the shopper's language ---
export function listenBlock(plain, fallbackText) {
  const lang = langSelect("Language to listen in");
  const btn = el("button", { type: "button", className: "listen", textContent: "🔊 Listen" });
  const note = el("span", { className: "muted", "aria-live": "polite" });
  btn.onclick = async () => {
    btn.disabled = true;
    note.textContent = "";
    try {
      const body = plain?.say ? { plain, language: lang.value } : { text: plain?.title ? `${plain.title}. ${plain.why || ""}` : fallbackText, language: lang.value };
      const v = lang.value === "en" && plain?.say ? { text: plain.say, speech_locale: "en-IN" } : await post("/v1/voice/verdict", body, 30000);
      const ok = speak(v.text, v.speech_locale, () => { note.textContent = "This device has no voice for that language. The words are below."; });
      note.textContent = `${ok ? "Speaking: " : ""}“${v.text}”${v.machine_translation ? " (machine translation)" : ""}${v.fell_back ? ` ${v.fell_back}` : ""}`;
    } catch (err) { note.textContent = `Couldn't get the spoken answer (${err.message}).`; }
    btn.disabled = false;
  };
  return el("div", { className: "listenrow" }, btn, lang, note);
}

// --- "Checked by code, not guessed" badge on a country line ---
export function badgeEl(badge) {
  if (!badge) return null;
  const text = `⚙ ${badge.text || "Checked by code, not guessed"}`;
  return badge.link?.url && /^https:/.test(badge.link.url)
    ? el("a", { className: "codebadge", href: badge.link.url, target: "_blank", rel: "noopener", title: `Open the official source: ${badge.link.label}`, textContent: text })
    : el("span", { className: "codebadge", title: "The status on this line was set by matching rules in code, not written by AI", textContent: text });
}

// --- I already bought it ---
let currentListing = null;
export const setListing = (listing) => { currentListing = listing || null; };

const download = (name, text) => {
  const a = el("a", { href: URL.createObjectURL(new Blob([text], { type: "text/markdown" })), download: name });
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
};

function draftCard(d) {
  const ja = d.translations?.ja;
  const body = el("textarea", { className: "draft", rows: 10, value: d.body, "aria-label": `${d.subject} (editable draft)` });
  const tabs = ja ? el("div", { className: "actions" },
    el("button", { type: "button", className: "small", textContent: "English", onclick: () => { body.value = d.body; } }),
    el("button", { type: "button", className: "small", textContent: "日本語", onclick: () => { body.value = ja.body; } })) : null;
  return el("div", { className: "draftcard" },
    el("h4", { textContent: d.kind === "refund_request" ? `Refund request to ${d.to}` : `Complaint to ${d.to}` }),
    el("p", { className: "muted", textContent: d.status }),
    ...(d.how?.length ? [el("ul", { className: "how" }, ...d.how.map((h) => el("li", { textContent: h })))] : []),
    ...(d.note ? [el("p", { className: "muted", textContent: d.note })] : []),
    el("p", {}, el("b", { textContent: "Subject: " }), d.subject), tabs, body,
    el("div", { className: "actions" }, copyBtnFor(body), el("span", { className: "muted", textContent: `Fill in: ${(d.fill_in || []).join(", ")}` })));
}

function incidentForm(product) {
  const f = el("form", { className: "incident" });
  const photo = el("input", { type: "file", accept: "image/*", capture: "environment", name: "photo" });
  const text = el("textarea", { name: "description", rows: 3, required: true, maxLength: 2000, placeholder: "What happened? e.g. it got very hot while charging and the plastic melted" });
  const out = el("div", { "aria-live": "polite" });
  f.append(el("h4", { textContent: "Something happened? Report it" }),
    el("p", { className: "muted", textContent: "Gemini checks your report and photo; code adds similar reports up into an early warning before any official recall. The photo isn't stored, and names and phone numbers are removed." }),
    el("label", {}, "What happened ", text), el("label", {}, "Photo (optional) ", photo),
    el("div", { className: "actions" }, el("button", { type: "submit", className: "primary", textContent: "Send report" })), out);
  f.onsubmit = async (ev) => {
    ev.preventDefault();
    out.textContent = "Checking your report…";
    try {
      const body = { ...product, description: text.value };
      if (photo.files[0]) body.photo = await shrink(photo.files[0]);
      const r = await post("/v1/incidents", body);
      const s = r.signal || {};
      out.replaceChildren(el("p", {}, el("b", { textContent: "Report received. " }), r.read?.summary || ""),
        el("p", { className: "muted", textContent: `Read as: ${(r.read?.hazard_type || "").replace("_", " ")}, ${r.read?.severity} severity${r.read?.first_hand ? ", first-hand" : ""}${r.read?.photo_damage && r.read.photo_damage !== "no_photo" ? `, photo shows ${r.read.photo_damage.replace(/_/g, " ")}` : ""}.` }),
        el("p", { className: s.early_warning ? "check red" : "muted", textContent: `This model: ${s.reports} report(s), ${s.serious_independent} independent serious. ${s.status}.` }));
    } catch (err) { out.textContent = `Couldn't send it (${err.message}).`; }
  };
  return f;
}

export function afterBlock(result) {
  const listing = currentListing || {};
  const box = el("div");
  const btn = el("button", { type: "button", textContent: "I already bought it: what now?" });
  btn.onclick = async () => {
    btn.disabled = true;
    btn.textContent = "Writing your steps and drafts…";
    try {
      const a = await post("/v1/after-purchase", { investigation_id: result.investigation_id, ...listing, purchase: { url: listing.url } }, 150000);
      const product = { brand: listing.brand, model: listing.model, title: listing.title, market: listing.market };
      box.replaceChildren(el("div", { className: "after" },
        el("h3", { textContent: a.headline }),
        el("ol", { className: "steps" }, ...a.steps.map((s) => el("li", {}, el("b", { textContent: s.title }), el("br"), s.detail,
          ...(s.url ? [" ", el("a", { href: s.url, target: "_blank", rel: "noopener", textContent: "Open the notice" })] : [])))),
        listenBlock(null, a.say),
        ...a.drafts.map(draftCard),
        el("div", { className: "actions" },
          el("button", { type: "button", className: "small", textContent: "Download the case file", onclick: () => download(`safeshelf-case-${a.investigation_id || "file"}.md`, a.case_file.markdown) }),
          el("span", { className: "muted", textContent: a.label })),
        incidentForm(product)));
      btn.remove();
    } catch (err) { btn.disabled = false; btn.textContent = `Couldn't load it (${err.message}). Try again`; }
  };
  return el("div", { className: "afterwrap" }, btn, box);
}
function copyBtnFor(ta) {
  const b = el("button", { type: "button", className: "small", textContent: "Copy the draft" });
  b.onclick = async () => { try { await navigator.clipboard.writeText(ta.value); b.textContent = "Copied ✓"; } catch (_) { ta.select(); b.textContent = "Selected: copy it"; } };
  return b;
}

// A phone photo is several MB; the label reader needs about 1280 px.
export async function shrink(file, max = 1280) {
  const img = await createImageBitmap(file);
  const scale = Math.min(1, max / Math.max(img.width, img.height));
  const c = el("canvas", { width: Math.round(img.width * scale), height: Math.round(img.height * scale) });
  c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
  return c.toDataURL("image/jpeg", 0.85);
}

// --- Ask out loud: Gemini Live, voice + camera ---
const WORKLET = `class Mic extends AudioWorkletProcessor { process(inputs) { const ch = inputs[0][0]; if (ch) this.port.postMessage(ch.slice(0)); return true; } }
registerProcessor("mic", Mic);`;
const b64 = (buf) => { let s = ""; const bytes = new Uint8Array(buf); for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000)); return btoa(s); };

export function setUpAsk() {
  const root = document.getElementById("ask");
  if (!root) return;
  const lang = langSelect("Language to talk in");
  const market = el("select", { "aria-label": "Your country" }, ...[["IN", "India"], ["JP", "Japan"], ["AU", "Australia"], ["SG", "Singapore"], ["NZ", "New Zealand"], ["US", "United States"]].map(([v, n]) => el("option", { value: v, textContent: n })));
  const video = el("video", { className: "cam", autoplay: true, muted: true, playsInline: true, "aria-label": "Camera preview" });
  const talk = el("button", { type: "button", className: "primary big", textContent: "🎙 Start talking" });
  const status = el("p", { className: "status", "aria-live": "assertive", textContent: "Press Start, point the camera at the label, and ask “Is this safe?”" });
  const log = el("div", { className: "talklog", "aria-live": "polite" });
  const card = el("div");
  // Photo fallback: one photo and one question, answered aloud (no Live needed)
  const photo = el("input", { type: "file", accept: "image/*", capture: "environment", "aria-label": "Take a photo of the label" });
  const question = el("input", { type: "text", value: "Is this safe?", "aria-label": "Your question", maxLength: 300 });
  const askBtn = el("button", { type: "button", className: "big", textContent: "📷 Ask with a photo" });
  const micBtn = "webkitSpeechRecognition" in window || "SpeechRecognition" in window ? el("button", { type: "button", textContent: "🎤 Say the question" }) : null;
  root.append(el("div", { className: "askgrid" },
    el("div", { className: "card askcard" }, el("h2", { textContent: "Ask out loud" }),
      el("p", { className: "muted", textContent: "Talk to SafeShelf like a shop assistant. Gemini Live listens and answers by voice in your language, but it can only say what SafeShelf's code found in official recall lists. Made for shoppers who'd rather not read small print: older shoppers, people who read little, and people who can't see the screen." }),
      el("div", { className: "actions" }, lang, market), video, el("div", { className: "actions" }, talk), status, log, card),
    el("div", { className: "card askcard" }, el("h3", { textContent: "No microphone? Ask with a photo" }),
      el("p", { className: "muted", textContent: "Take a photo of the label and ask. The answer is read aloud." }),
      el("label", {}, "Photo of the label ", photo), el("label", {}, "Question ", question),
      el("div", { className: "actions" }, askBtn, micBtn))));

  const showCard = (plain, label) => {
    if (!plain) return;
    card.replaceChildren(el("div", { className: `plain` },
      el("h3", { className: `ptitle ${plain.tone}`, textContent: plain.title }),
      el("p", { className: "muted", textContent: label ? `Read from the label: ${[label.brand, label.model, label.batch && `batch ${label.batch}`].filter(Boolean).join(" ")}` : "" }),
      el("p", { textContent: plain.why }), el("p", {}, el("b", { textContent: "What you can do: " }), plain.todo),
      ...(plain.link?.url ? [el("a", { href: plain.link.url, target: "_blank", rel: "noopener", textContent: plain.link.label })] : []),
      ...(plain.checked || []).slice(0, 4).map((c) => el("p", { className: "muted" }, `${c.flag} ${c.name}: ${c.status} `, badgeEl(c.badge)))));
  };
  const line = (who, text) => {
    const last = log.lastElementChild;
    if (last?.dataset.who === who && !last.dataset.closed) { last.querySelector("span").textContent += text; return; }
    const p = el("p", { className: who }, el("b", { textContent: who === "you" ? "You: " : "SafeShelf: " }), el("span", { textContent: text }));
    p.dataset.who = who;
    log.append(p);
  };
  const closeLines = () => { for (const p of log.children) p.dataset.closed = "1"; };

  let session = null;
  const stop = (why) => {
    if (!session) return;
    const s = session;
    session = null;
    clearInterval(s.frames);
    try { s.ws.send(JSON.stringify({ type: "end" })); } catch (_) { /* closed */ }
    try { s.ws.close(); } catch (_) { /* closed */ }
    s.streams.forEach((st) => st.getTracks().forEach((t) => t.stop()));
    s.mic?.close();
    s.out?.close();
    video.srcObject = null;
    talk.textContent = "🎙 Start talking";
    if (why) status.textContent = why;
  };

  talk.onclick = async () => {
    if (session) return stop("Stopped. Press Start to talk again.");
    status.textContent = "Starting the microphone and camera…";
    const streams = [];
    try {
      const audio = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      streams.push(audio);
      let cam = null;
      try { cam = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: { ideal: 1280 } } }); streams.push(cam); video.srcObject = cam; } catch (_) { status.textContent = "No camera: you can still say the brand and model."; }
      const mic = new AudioContext({ sampleRate: 16000 });
      await mic.audioWorklet.addModule(URL.createObjectURL(new Blob([WORKLET], { type: "text/javascript" })));
      const out = new AudioContext({ sampleRate: 24000 });
      const ws = new WebSocket(`${API.replace(/^http/, "ws")}/v1/live?language=${encodeURIComponent(lang.value)}&market=${market.value}`);
      session = { ws, streams, mic, out, playAt: 0, frames: null };
      const s = session;
      ws.onmessage = (ev) => {
        const m = JSON.parse(ev.data);
        if (m.type === "ready") {
          talk.textContent = "■ Stop";
          status.textContent = cam ? "Listening. Point the camera at the label and ask “Is this safe?”" : "Listening. Say the brand and model number.";
          const node = new AudioWorkletNode(mic, "mic");
          mic.createMediaStreamSource(audio).connect(node);
          node.port.onmessage = (e) => {
            if (ws.readyState !== 1) return;
            const f = e.data, pcm = new Int16Array(f.length);
            for (let i = 0; i < f.length; i++) pcm[i] = Math.max(-1, Math.min(1, f[i])) * 0x7fff;
            ws.send(JSON.stringify({ type: "audio", data: b64(pcm.buffer) }));
          };
          if (cam) {
            const c = el("canvas");
            s.frames = setInterval(() => {
              if (!video.videoWidth || ws.readyState !== 1) return;
              const scale = Math.min(1, 1024 / video.videoWidth);
              c.width = Math.round(video.videoWidth * scale); c.height = Math.round(video.videoHeight * scale);
              c.getContext("2d").drawImage(video, 0, 0, c.width, c.height);
              ws.send(JSON.stringify({ type: "frame", data: c.toDataURL("image/jpeg", 0.8) }));
            }, 1000);
          }
        } else if (m.type === "audio") {
          const bytes = Uint8Array.from(atob(m.data), (ch) => ch.charCodeAt(0));
          const pcm = new Int16Array(bytes.buffer);
          const buf = out.createBuffer(1, pcm.length, 24000);
          const ch = buf.getChannelData(0);
          for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 0x8000;
          const src = out.createBufferSource();
          src.buffer = buf;
          src.connect(out.destination);
          s.playAt = Math.max(s.playAt, out.currentTime);
          src.start(s.playAt);
          s.playAt += buf.duration;
        } else if (m.type === "heard") line("you", m.text);
        else if (m.type === "said") line("safeshelf", m.text);
        else if (m.type === "turn_complete") closeLines();
        else if (m.type === "result") { status.textContent = "Checked official recall lists."; showCard(m.plain, m.label); }
        else if (m.type === "error") stop(`${m.detail} The photo check below still works.`);
      };
      ws.onerror = () => stop("Couldn't reach Gemini Live. Use the photo check below; it answers aloud too.");
      ws.onclose = () => { if (session === s) stop("The conversation ended (it lasts up to 3 minutes). Press Start to talk again."); };
    } catch (err) {
      streams.forEach((st) => st.getTracks().forEach((t) => t.stop()));
      session = null;
      status.textContent = `Couldn't start (${err.message}). Allow the microphone, or use the photo check below.`;
    }
  };

  // Turn-based fallback: photo + question -> POST /v1/camera/ask -> spoken answer. Follow-ups reuse the label.
  let last = null;
  if (micBtn) micBtn.onclick = () => {
    const R = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new R();
    rec.lang = (LANGS.find(([c]) => c === lang.value) || LANGS[0])[2];
    micBtn.textContent = "🎤 Listening…";
    rec.onresult = (e) => { question.value = e.results[0][0].transcript; };
    rec.onend = () => { micBtn.textContent = "🎤 Say the question"; };
    rec.start();
  };
  askBtn.onclick = async () => {
    if (!photo.files[0] && !last) { status.textContent = "Take a photo of the label first."; photo.focus(); return; }
    askBtn.disabled = true;
    status.textContent = "Reading the label and checking official recall lists…";
    try {
      const body = { question: question.value, language: lang.value, market: market.value };
      if (photo.files[0]) Object.assign(body, { image: await shrink(photo.files[0]) });
      else Object.assign(body, { label: last.label, investigation_id: last.investigation_id });
      const a = await post("/v1/camera/ask", body, 150000);
      last = a;
      photo.value = "";
      line("you", a.heard); closeLines(); line("safeshelf", a.answer.text); closeLines();
      speak(a.answer.text, a.answer.speech_locale, () => { status.textContent = "This device has no voice for that language; the answer is written above."; });
      showCard(a.plain, a.label);
      status.textContent = "Ask another question, or take a new photo.";
    } catch (err) { status.textContent = `Couldn't answer (${err.message}).`; }
    askBtn.disabled = false;
  };
}

// --- Attacker vs defender ---
const ATTACK_NAMES = { forged_regulator: "Forged regulator page", lookalike_model: "Look-alike model number", injected_instructions: "Hidden instructions in a notice",
  copied_complaints: "Reposted complaints", fake_shop: "Fake shop that talks to AI" };
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

function roundRow(r) {
  return el("li", { className: `round ${r.held ? "held" : "beaten"}` },
    el("div", { className: "atk" }, el("small", { textContent: r.control ? "Control" : "Attacker" }), r.attack),
    el("div", { className: "def" }, el("small", { textContent: "Defender (code)" }), `${(r.basis || r.outcome || "").replace(/_/g, " ")}`,
      el("span", { className: "verdictmark", textContent: r.held ? " ✓ as designed" : " ✗ not as designed" })),
    el("div", { className: "must muted", textContent: r.defence_must }));
}

export async function setUpRedteam(takeQuota) {
  const root = document.getElementById("redteam");
  if (!root) return;
  let data;
  try { data = await (await fetch(`${API}/v1/redteam/rounds`, { signal: AbortSignal.timeout(20000) })).json(); if (!data.rounds) throw new Error(); }
  catch (_) { try { data = await (await fetch("data/redteam.json")).json(); } catch (_e) { root.replaceChildren(el("p", { className: "error", textContent: "The red-team results could not be loaded." })); return; } }
  const score = el("b", { className: "score", textContent: "0 / 0" });
  const list = el("ol", { className: "rounds" });
  const replay = el("button", { type: "button", className: "primary", textContent: "▶ Replay the 18 rounds" });
  const kind = el("select", { "aria-label": "Attack to try" }, ...Object.entries(ATTACK_NAMES).map(([k, n]) => el("option", { value: k, textContent: n })));
  const go = el("button", { type: "button", className: "primary", textContent: "Let Gemini attack now" });
  const liveBox = el("div", { "aria-live": "polite" });
  root.replaceChildren(
    el("h2", { className: "vs-head", textContent: "Attacker vs defender" }),
    el("p", { className: "muted", textContent: "Every SafeShelf answer comes from code that checks whether a source is official, whether a notice covers this exact model, and whether reports are really independent. Here we attack that code: forged regulator pages, look-alike models, hidden instructions, copied complaints, fake shops. Left: what the attack tried. Right: what the code decided." }),
    el("div", { className: "vs-grid" },
      el("div", { className: "vs-card card" }, el("h3", {}, "Saved red-team: ", score), el("p", { className: "muted", textContent: `${data.metrics.hard_negatives} of these are traps that must not become a recall; the others are controls that must still be caught. Invented hard cases: they show the rules behave as designed, not real-world accuracy.` }),
        el("div", { className: "actions" }, replay), list),
      el("div", { className: "vs-card card" }, el("h3", { textContent: "Live round: Gemini is the attacker" }),
        el("p", { className: "muted", textContent: "Gemini invents a new attack of the kind you pick. The same code that answers shoppers defends; whether it held is decided by a fixed rule, not by either model." }),
        el("div", { className: "actions" }, kind, go, el("span", { className: "quota", "data-quota": "" })), liveBox,
        el("details", {}, el("summary", { textContent: "What the defence doesn't claim" }), el("ul", { className: "caveats" }, ...(data.limits || []).map((t) => el("li", { textContent: t })))))));
  const draw = async (animate) => {
    list.replaceChildren();
    let held = 0;
    for (const [i, r] of data.rounds.entries()) {
      if (animate) await wait(450);
      list.append(roundRow(r));
      held += r.held ? 1 : 0;
      score.textContent = `${held} / ${i + 1} as designed`;
    }
  };
  replay.onclick = () => draw(true);
  draw(false);
  go.onclick = async () => {
    if (takeQuota && !takeQuota()) { liveBox.replaceChildren(el("p", { className: "error", textContent: "Live runs are used up on this browser today." })); return; }
    go.disabled = true;
    liveBox.replaceChildren(el("p", { className: "muted", textContent: "Gemini is writing an attack…" }));
    try {
      const r = await post("/v1/redteam/round", { attack: kind.value, market: "US" }, 90000);
      const a = r.attacker, d = r.defender;
      const shown = [["Product", `${a.brand} ${a.model_number}`], ["Notice title", a.notice_title], ["Notice address", a.notice_url], ["Notice model", a.notice_model_number],
        ["Notice text", a.notice_text], ["Shop", a.shop_url], ["Seller", a.seller], ["Hidden page text", a.page_text]].filter(([, v]) => v);
      liveBox.replaceChildren(el("div", { className: "liveround" },
        el("div", { className: "atk" }, el("small", { textContent: `Attacker: ${a.model}` }), el("p", { textContent: a.attack_summary }),
          el("dl", {}, ...shown.flatMap(([k, v]) => [el("dt", { textContent: k }), el("dd", { textContent: String(v).slice(0, 400) })])),
          ...(a.complaints?.length ? [el("ol", { className: "posts" }, ...a.complaints.map((c) => el("li", { textContent: c })))] : [])),
        el("div", { className: `def ${d.held ? "held" : "beaten"}` }, el("small", { textContent: "Defender: SafeShelf's code" }),
          el("p", { className: "big", textContent: d.held ? "✓ Defence held" : "✗ The attack got through" }),
          el("p", { textContent: d.rule }),
          el("p", { className: "muted", textContent: Object.entries(d.decision).filter(([k]) => !["headline", "seller_reason"].includes(k)).map(([k, v]) => `${k.replace(/_/g, " ")}: ${Array.isArray(v) ? v.join(", ") || "none" : typeof v === "object" ? JSON.stringify(v) : v}`).join(" · ") }),
          ...(d.attack_valid ? [] : [el("p", { className: "muted", textContent: "Note: this attack didn't follow its own brief, so it doesn't count either way." })]))));
    } catch (err) { liveBox.replaceChildren(el("p", { className: "error", textContent: `The round couldn't run (${err.message}).` })); }
    go.disabled = false;
  };
}
