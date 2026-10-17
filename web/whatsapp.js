// SafeShelf judges' page, part 3: "On WhatsApp", the WhatsApp bot (whatsapp/) working in a phone on the page.
// It makes the same live API calls as whatsapp/app.py handle(), in the same order, and writes its replies with the
// same words as whatsapp/bot.py (ported below: keep the two in step). Differences from the real number, said on the
// page: the voice note is spoken by this device's voice (the bot sends Gemini TTS audio); a real shop link is read by
// the API (POST /v1/listings/read), or checked by its link alone when that reader isn't deployed; the test-page
// links use the page the test was written for. Nothing is sent to WhatsApp. Text is always set as text, never HTML.
import { API, LANGS, el, shrink } from "./actions.js?v=20261017v";

// ---------- whatsapp/bot.py, in JavaScript ----------

const URL_RE = /https?:\/\/[^\s<>"']+/;
// code -> [English name, name in its own script] (bot.LANGUAGES)
const LANGUAGES = {
  en: ["English", "English"], hi: ["Hindi", "हिन्दी"], bn: ["Bengali", "বাংলা"], mr: ["Marathi", "मराठी"],
  te: ["Telugu", "తెలుగు"], ta: ["Tamil", "தமிழ்"], gu: ["Gujarati", "ગુજરાતી"], ur: ["Urdu", "اردو"],
  kn: ["Kannada", "ಕನ್ನಡ"], or: ["Odia", "ଓଡ଼ିଆ"], ml: ["Malayalam", "മലയാളം"], pa: ["Punjabi", "ਪੰਜਾਬੀ"],
  ne: ["Nepali", "नेपाली"], si: ["Sinhala", "සිංහල"], ja: ["Japanese", "日本語"], ko: ["Korean", "한국어"],
  "zh-Hans": ["Chinese (Simplified)", "简体中文"], "zh-Hant": ["Chinese (Traditional)", "繁體中文"],
  id: ["Indonesian", "Bahasa Indonesia"], ms: ["Malay", "Bahasa Melayu"], th: ["Thai", "ไทย"],
  vi: ["Vietnamese", "Tiếng Việt"], fil: ["Filipino", "Filipino"], my: ["Burmese", "မြန်မာ"],
  km: ["Khmer", "ខ្មែរ"], lo: ["Lao", "ລາວ"],
};
const NAMES = Object.assign(Object.fromEntries(Object.entries(LANGUAGES).flatMap(([code, names]) => names.map((n) => [n.toLowerCase(), code]))), {
  "हिंदी": "hi", bangla: "bn", oriya: "or", chinese: "zh-Hans", "中文": "zh-Hans", bahasa: "id",
  tagalog: "fil", myanmar: "my", nihongo: "ja", thai: "th", "ภาษาไทย": "th" });
const SCRIPTS = [
  [/[぀-ヿ]/, "ja", []], [/[가-힯ᄀ-ᇿ]/, "ko", []], [/[一-鿿]/, "zh-Hans", ["ja", "zh-Hant"]],
  [/[ऀ-ॿ]/, "hi", ["mr", "ne"]], [/[ঀ-৿]/, "bn", []], [/[਀-੿]/, "pa", []], [/[઀-૿]/, "gu", []],
  [/[଀-୿]/, "or", []], [/[஀-௿]/, "ta", []], [/[ఀ-౿]/, "te", []], [/[ಀ-೿]/, "kn", []],
  [/[ഀ-ൿ]/, "ml", []], [/[඀-෿]/, "si", []], [/[฀-๿]/, "th", []], [/[຀-໿]/, "lo", []],
  [/[က-႟]/, "my", []], [/[ក-៿]/, "km", []], [/[؀-ۿ]/, "ur", []],
  [/[ăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]/i, "vi", []],
];
const HAZARD_WORDS = {
  en: { fire_burn: "overheating, fire or burns", electric_shock: "electric shocks", choking: "choking", chemical: "chemical harm", mechanical_injury: "injuries", other: "safety problems" },
  hi: { fire_burn: "ज़्यादा गरम होने, आग या जलने", electric_shock: "बिजली के झटके", choking: "गला अटकने", chemical: "रासायनिक नुकसान", mechanical_injury: "चोट", other: "सुरक्षा समस्याओं" },
};
const TEXT = {
  en: {
    help: "Send me a product link or a photo of the product or its label. I'll check: Is it safe? Is it real?\nWrite in your language, or reply with its name to switch: HINDI, TAMIL, BANGLA, 日本語, 한국어, 中文, BAHASA, ไทย, TIẾNG VIỆT, FILIPINO…",
    working: "Checking this product. One moment…",
    unknown: "I couldn't tell which product this is. Try a clearer photo of the label (brand and model number), or send the shop link.",
    red: "⛔ RECALLED. {name} is on an official recall list ({recalls}). Stop using it and follow the recall instructions.",
    amber: "⚠️ BE CAREFUL. {n} buyers reported {hazard} with {name}. Under review, not an official recall.",
    green: "✅ CHECKED. No recall and no hazard reports found for {name} in {reviews} reviews.",
    not_enough_evidence: "ℹ️ NOT ENOUGH EVIDENCE. Too few reviews of {name} to judge its safety yet. No recall found.",
    under_review_recall: "A recall that may cover it is being checked.",
    abroad: "⚠️ RECALLED IN ANOTHER COUNTRY. {authority} recalled this model ({record}). Not confirmed for your country yet: check that your label shows the same model and batch, and don't charge it unattended until you know.",
    batch: "⚠️ RECALLED FOR SOME UNITS. {authority} recalled {name} for certain serial or batch numbers ({record}). Check the number on your unit against the notice.",
    checked: "Checked: {summary}",
    shop_ok: "Shop check: nothing unusual found.",
    shop: "Shop check: {summary}",
    hidden: "This page has hidden text aimed at AI assistants. I ignored it.",
    alternative: "Safer option: {name} ({why}).",
    footer: "AI findings are evidence for you, not an official ruling.",
    photo: "From your photo: {name}.",
  },
  hi: {
    help: "मुझे किसी प्रोडक्ट का लिंक या उसकी या उसके लेबल की फ़ोटो भेजें। मैं जाँचूँगा: क्या यह सुरक्षित है? क्या यह असली है?\nEnglish के लिए ENGLISH लिखें, या अपनी भाषा का नाम लिखें (TAMIL, BANGLA, 日本語…)।",
    working: "इस प्रोडक्ट की जाँच कर रहा हूँ। एक पल…",
    unknown: "मैं पहचान नहीं पाया कि यह कौन सा प्रोडक्ट है। लेबल (ब्रांड और मॉडल नंबर) की साफ़ फ़ोटो या दुकान का लिंक भेजें।",
    red: "⛔ रिकॉल हुआ है। {name} आधिकारिक रिकॉल सूची में है ({recalls})। इसका इस्तेमाल बंद करें और रिकॉल के निर्देश मानें।",
    amber: "⚠️ सावधान रहें। {n} खरीदारों ने {name} से {hazard} की शिकायत की है। जाँच चल रही है, यह आधिकारिक रिकॉल नहीं है।",
    green: "✅ जाँच हो गई। {name} के {reviews} रिव्यू में कोई रिकॉल या खतरे की शिकायत नहीं मिली।",
    not_enough_evidence: "ℹ️ पर्याप्त जानकारी नहीं। {name} की सुरक्षा बताने के लिए अभी बहुत कम रिव्यू हैं। कोई रिकॉल नहीं मिला।",
    under_review_recall: "एक रिकॉल जो इस पर लागू हो सकता है, उसकी जाँच चल रही है।",
    abroad: "⚠️ दूसरे देश में रिकॉल हुआ है। {authority} ने यह मॉडल रिकॉल किया है ({record})। आपके देश के लिए अभी पुष्टि नहीं हुई: लेबल पर वही मॉडल और बैच नंबर देखें, और तब तक इसे बिना निगरानी चार्ज न करें।",
    batch: "⚠️ कुछ यूनिट का रिकॉल हुआ है। {authority} ने {name} के कुछ सीरियल या बैच नंबर रिकॉल किए हैं ({record})। अपनी यूनिट का नंबर नोटिस से मिलाएँ।",
    checked: "जाँचे गए स्रोत: {summary}",
    shop_ok: "दुकान की जाँच: कुछ असामान्य नहीं मिला।",
    shop: "दुकान की जाँच: {summary}",
    hidden: "इस पेज में AI के लिए छिपा हुआ टेक्स्ट है। मैंने उसे अनदेखा किया।",
    alternative: "सुरक्षित विकल्प: {name} ({why})।",
    footer: "AI की जानकारी आपके लिए सबूत है, आधिकारिक फ़ैसला नहीं।",
    photo: "आपकी फ़ोटो से: {name}।",
  },
};
const SHOP_HI = [
  [/photos copied from the genuine product's marketplace listing, on a site that is not a known seller/g, "फ़ोटो असली प्रोडक्ट की मार्केटप्लेस लिस्टिंग से कॉपी की गई हैं, और यह साइट कोई जाना-माना विक्रेता नहीं है"],
  [/photos copied from the genuine product's official listing, but the seller is not authorised/g, "फ़ोटो असली प्रोडक्ट की आधिकारिक लिस्टिंग से कॉपी की गई हैं, पर विक्रेता अधिकृत नहीं है"],
  [/price is (\d+)% of the genuine product's lowest (?:marketplace price|price from an authorised seller)/g, "कीमत असली प्रोडक्ट की सबसे कम कीमत का $1% है"],
  [/website registered only (\d+) days ago/g, "वेबसाइट सिर्फ़ $1 दिन पहले बनी है"],
  [/specs differ from the genuine model \(([^)]*)\)/g, "स्पेसिफ़िकेशन असली मॉडल से अलग हैं ($1)"],
  [/^Be careful: /, "सावधान: "],
];
const HIDDEN_REASON = /;? ?the page hides instructions aimed at AI assistants/;
const fill = (s, v) => s.replace(/\{(\w+)\}/g, (_, k) => String(v[k] ?? ""));

function language(text, current = "en") {
  const words = text.trim().toLowerCase();
  if (NAMES[words]) return NAMES[words];
  for (const [script, code, keeps] of SCRIPTS) if (script.test(text)) return current === code || keeps.includes(current) ? current : code;
  return current;
}

function parse(msg) {
  if (msg.type === "image") return { kind: "photo", image: msg.image, caption: msg.caption || "" };
  const text = msg.text || "";
  const found = text.match(URL_RE);
  if (found) return { kind: "link", url: found[0].replace(/[).,]+$/, ""), text };
  if (NAMES[text.trim().toLowerCase()]) return { kind: "switch", text };
  return { kind: "help", text };
}

const productName = (identity, lang = "en") => [identity.brand, identity.model].filter(Boolean).join(" ") || (lang === "hi" ? "यह प्रोडक्ट" : "this product");

function shopLine(trust, lang) {
  if (!trust || !Object.keys(trust).length) return null;
  const t = TEXT[lang] || TEXT.en;
  let summary = (trust.summary || "").replace(HIDDEN_REASON, "");
  if (!summary.toLowerCase().startsWith("be careful") || ["Be careful:", "Be careful: ."].includes(summary.trim())) return t.shop_ok;
  if (lang === "hi") {
    for (const [pattern, hindi] of SHOP_HI) summary = summary.replace(pattern, hindi);
    summary = summary.replace(/\.$/, "") + "।";
  }
  return fill(t.shop, { summary });
}

function reply(identity, safety, lang = "en", { trust = null, alternatives = null, fromPhoto = false } = {}) {
  lang = TEXT[lang] ? lang : "en";
  const t = TEXT[lang], name = productName(identity, lang);
  const lines = fromPhoto ? [fill(t.photo, { name })] : [];
  const verdict = safety.verdict, status = safety.official_status || {}, lead = safety.lead_record || {}, basis = safety.basis;
  const words = safety.plain || {};
  const hasLead = Object.keys(lead).length > 0;
  const plainEn = Object.keys(words).length > 0 && lang === "en";
  if (plainEn) {
    const icon = { red: "⛔", amber: "⚠️", green: "✅" }[words.tone] || "ℹ️";
    lines.push(`${icon} ${words.title.toUpperCase()}. ${words.why}`);
    lines.push(`What you can do: ${words.todo}`);
    const places = (words.checked || []).slice(0, 5).map((c) => `${c.flag} ${c.name}: ${c.status.split(" (")[0]}`);
    if (places.length) lines.push("Where we checked:\n" + places.join("\n"));
    if (words.link) lines.push(`${words.link.label}: ${words.link.url}`);
  } else if (verdict === "red") {
    lines.push(fill(t.red, { name, recalls: lead.record_id || (status.recall_ids || []).join(", ") }));
  } else if (["recalled_abroad_same_model", "local_recall_batch_unknown"].includes(basis) && hasLead) {
    lines.push(fill(t[basis === "recalled_abroad_same_model" ? "abroad" : "batch"], { name, authority: lead.authority || "A regulator", record: lead.record_id || "" }));
  } else if (verdict === "amber") {
    const top = (safety.ai_findings || [{}])[0] || {};
    lines.push(fill(t.amber, { n: top.independent_reports || 0, name, hazard: HAZARD_WORDS[lang][top.hazard_type] || HAZARD_WORDS[lang].other }));
  } else if (verdict === "green") {
    lines.push(fill(t.green, { name, reviews: safety.reviews_checked || 0 }));
  } else lines.push(fill(t.not_enough_evidence, { name }));
  if ((status.recall_ids_under_review || []).length && verdict !== "red" && !hasLead) lines.push(t.under_review_recall);
  const summary = (safety.coverage || {}).summary;
  if (summary && !plainEn) lines.push(fill(t.checked, { summary }));
  const shop = shopLine(trust || {}, lang);
  if (shop) lines.push(shop);
  if (trust?.hidden_instructions_found) lines.push(t.hidden);
  const best = ((alternatives || {}).alternatives || [])[0];
  if (best && ["red", "amber"].includes(verdict)) {
    const why = lang === "en" ? `0 hazard reports in ${best.reviews_read} reviews` : `${best.reviews_read} रिव्यू में 0 खतरे की शिकायत`;
    lines.push(fill(t.alternative, { name: `${best.brand} ${best.model}`.trim(), why }));
  }
  lines.push(t.footer);
  return lines.join("\n\n");
}

const voiceText = (text) => text.replace(/[⛔⚠️✅ℹ️]/gu, "").replaceAll("\n\n", " ").trim();

// ---------- the live API, as whatsapp/app.py calls it ----------

async function call(path, body, timeout = 120000) {
  const res = await fetch(`${API}${path}`, body === undefined ? { signal: AbortSignal.timeout(timeout) }
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: AbortSignal.timeout(timeout) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(typeof data.detail === "string" ? data.detail : `the API answered ${res.status}`), { status: res.status });
  return data;
}

// The real bot has Gemini translate the English reply into the other JAPAC languages. Here the API's translator for
// spoken answers does it (POST /v1/voice/verdict with text), one paragraph at a time so the line breaks stay. English
// if it fails, as in the bot.
const translated = new Map();
async function translate(text, lang) {
  if (TEXT[lang] || !LANGUAGES[lang]) return text;
  if (translated.has(`${lang}\n${text}`)) return translated.get(`${lang}\n${text}`);
  try {
    const parts = await Promise.all(text.split("\n\n").map((p) => call("/v1/voice/verdict", { text: p, language: lang }, 30000).then((v) => v.text || p)));
    const out = parts.join("\n\n");
    if (Object.values(TEXT.en).includes(text)) translated.set(`${lang}\n${text}`, out);
    return out;
  } catch (_) { return text; }
}
const fixed = (lang, key) => (TEXT[lang] ? Promise.resolve(TEXT[lang][key]) : translate(TEXT.en[key], lang));

// ---------- the phone ----------

const ICON = {
  back: "M15 5l-7 7 7 7", video: "M3 7h11v10H3zM14 10l6-3v10l-6-3", call: "M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a1 1 0 0 1-1 1A16 16 0 0 1 4 5a1 1 0 0 1 1-1z",
  dots: "M12 5h.01M12 12h.01M12 19h.01", smile: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM8.5 14.5a4.5 4.5 0 0 0 7 0M9 9.5h.01M15 9.5h.01",
  clip: "M20 11.5l-8 8a5 5 0 0 1-7-7l8.5-8.5a3.3 3.3 0 0 1 4.7 4.7L9.7 17a1.7 1.7 0 0 1-2.4-2.4l7.4-7.4",
  camera: "M4 8h3l2-3h6l2 3h3v11H4zM12 17a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z",
  mic: "M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM6 11a6 6 0 0 0 12 0M12 17v4", send: "M4 20l17-8L4 4l2 8zM6 12h8",
  play: "M8 5v14l11-7z", pause: "M7 5h4v14H7zM13 5h4v14h-4z",
};
const svg = (d, cls = "") => {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("viewBox", "0 0 24 24");
  s.setAttribute("aria-hidden", "true");
  if (cls) s.setAttribute("class", cls);
  const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
  p.setAttribute("d", d);
  s.append(p);
  return s;
};
const LOGO = () => {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("viewBox", "0 0 32 32");
  s.setAttribute("aria-hidden", "true");
  s.innerHTML = '<rect width="32" height="32" fill="#0271E4"/><path d="M8 10a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v5c0 5-4 8.5-8 10-4-1.5-8-5-8-10z" fill="#fff"/><path d="m12 15.5 3 3 5-5.5" fill="none" stroke="#0271E4" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>';
  return s;
};
const clock = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const localeOf = (lang) => (LANGS.find(([c]) => c === lang) || LANGS[0])[2];

// Message text with its links made tappable (as text nodes and anchors, never HTML).
function richText(text) {
  const p = el("span", { className: "wa-text" });
  let rest = text;
  for (let m = rest.match(URL_RE); m; m = rest.match(URL_RE)) {
    p.append(rest.slice(0, m.index));
    const url = m[0].replace(/[).,]+$/, "");
    p.append(/^https:/.test(url) ? el("a", { href: url, target: "_blank", rel: "noopener", textContent: url }) : url);
    rest = rest.slice(m.index + url.length);
  }
  p.append(rest);
  return p;
}

export function setUpWhatsApp(takeQuota = () => true, usedUpText = () => "") {
  const root = document.getElementById("wa");
  if (!root) return;
  let lang = "en";
  let presets = [];
  fetch("samples/presets.json").then((r) => r.json()).then((d) => { presets = d.presets || []; }).catch(() => {});

  // --- the phone ---
  const sub = el("small", { className: "wa-sub", textContent: "Business account" });
  const head = el("div", { className: "wa-head" },
    el("span", { className: "wa-ico" }, svg(ICON.back)), el("span", { className: "wa-av" }, LOGO()),
    el("span", { className: "wa-who" }, el("b", {}, "SafeShelf ", el("span", { className: "wa-tick-badge", title: "Verified business (demo)", textContent: "✓" })), sub),
    el("span", { className: "wa-ico" }, svg(ICON.video)), el("span", { className: "wa-ico" }, svg(ICON.call)), el("span", { className: "wa-ico" }, svg(ICON.dots)));
  const log = el("div", { className: "wa-chat", role: "log", "aria-live": "polite", "aria-label": "Chat with SafeShelf" },
    el("div", { className: "wa-day", textContent: "Today" }),
    el("div", { className: "wa-sys", textContent: "🔒 A demo chat on this page: answers come from the live SafeShelf API. Nothing is sent to WhatsApp." }),
    el("div", { className: "wa-intro" }, el("span", { className: "wa-av big" }, LOGO()), el("b", { textContent: "SafeShelf" }),
      el("span", { textContent: "Is it safe? Is it real? Send a product link or a photo of the label." })));
  const input = el("textarea", { className: "wa-input", rows: 1, placeholder: "Message", "aria-label": "Message to SafeShelf", maxLength: 1000 });
  const photo = el("input", { type: "file", accept: "image/*", className: "sr", "aria-label": "Send a photo of the product or its label" });
  const camera = el("input", { type: "file", accept: "image/*", capture: "environment", className: "sr", "aria-label": "Take a photo of the label" });
  const sendBtn = el("button", { type: "submit", className: "wa-send", "aria-label": "Send" }, svg(ICON.mic));
  const form = el("form", { className: "wa-compose" },
    el("div", { className: "wa-field" }, el("span", { className: "wa-ico dim" }, svg(ICON.smile)), input,
      el("label", { className: "wa-ico dim", title: "Send a photo" }, svg(ICON.clip), photo),
      el("label", { className: "wa-ico dim", title: "Take a photo" }, svg(ICON.camera), camera)),
    sendBtn);
  const status = el("div", { className: "wa-status", "aria-hidden": "true" }, el("b", { textContent: clock() }), el("span", { textContent: "▴ ◔ ▮" }));
  const phone = el("div", { className: "wa-phone" }, el("div", { className: "wa-screen" }, status, head, log, form));

  // --- quick tries, beside the phone ---
  const chips = el("div", { className: "wa-chips", role: "group", "aria-label": "Messages to try" });
  const TRIES = [
    ["Hi", "Hi"],
    ["Anker power bank, Flipkart", "Is this safe? https://www.flipkart.com/anker-powercore-10000-a1263/p/itm0001"],
    ["HAIARA W5PRO, Amazon.co.jp", "https://www.amazon.co.jp/dp/SAFESHELF-W5PRO"],
    ["₹299 'original' charger deal", "Bhai ye original hai? https://example-deals-store.test/65w-charger"],
    ["Kelvo charger, official store", "https://demo.safeshelf.app/product/cx-65"],
    ["SafeVolt charger (safe)", "https://demo.safeshelf.app/product/sv-65"],
    ["Switch to हिन्दी", "हिन्दी"], ["Switch to TAMIL", "TAMIL"], ["Back to ENGLISH", "ENGLISH"],
  ];
  for (const [label, text] of TRIES) chips.append(el("button", { type: "button", className: "wa-chip", textContent: label, title: text, onclick: () => send({ type: "text", text }) }));

  const steps = el("ol", { className: "wa-steps", "aria-live": "polite" });
  const step = (text, state = "run") => {
    const li = el("li", { className: state }, el("span", { textContent: text }));
    steps.append(li);
    steps.scrollTop = steps.scrollHeight;
    return { done: (more, cls = "ok") => { li.className = cls; if (more) li.append(el("small", { textContent: more })); } };
  };
  const timed = async (label, work) => {
    const s = step(label), t0 = performance.now();
    try { const out = await work(); s.done(`${((performance.now() - t0) / 1000).toFixed(1)} s`); return out; } catch (err) { s.done(err.message, "bad"); throw err; }
  };
  const side = el("aside", { className: "wa-side" },
    el("h3", { textContent: "Try a message" }),
    el("p", { className: "muted", textContent: "Tap one, type your own, paste any product link, or send a photo of a label with 📎 or 📷. Type a language name (TAMIL, 日本語, BAHASA…) to switch." }),
    chips,
    el("h3", { textContent: "Behind the chat" }),
    el("p", { className: "muted", textContent: "The same live API calls the WhatsApp bot makes, in the same order. Code picks every word of the answer." }),
    steps,
    el("details", { className: "wa-diff" }, el("summary", { textContent: "How this differs from the real number" }),
      el("ul", {},
        el("li", { textContent: "Same words and steps as the bot (whatsapp/bot.py and app.py). The WhatsApp number is waiting on Meta's test-number approval." }),
        el("li", { textContent: "The voice note uses this device's voice. On WhatsApp it's a Gemini voice recording." }),
        el("li", { textContent: "The test links above use the page each test was written for. Other links are read live by the API when it can open them." }),
        el("li", { textContent: "Each link or photo uses one check. Hi and language switches are free." }))));
  root.replaceChildren(el("div", { className: "wa-wrap" }, phone, side));

  // --- bubbles ---
  const scroll = () => { log.scrollTop = log.scrollHeight; };
  const meta = (mine) => {
    const m = el("span", { className: "wa-meta" }, clock());
    if (mine) m.append(el("span", { className: "wa-ticks", textContent: "✓" }));
    return m;
  };
  const bubble = (mine, ...kids) => {
    const b = el("div", { className: `wa-msg ${mine ? "out" : "in"}` }, ...kids, meta(mine));
    log.append(b);
    scroll();
    return b;
  };
  const botText = (text) => bubble(false, richText(text));
  let typing = null;
  const setTyping = (what) => {
    sub.textContent = what || "Business account";
    sub.classList.toggle("live", Boolean(what));
    if (what && !typing) { typing = el("div", { className: "wa-msg in wa-typing", "aria-label": what }, el("i"), el("i"), el("i")); log.append(typing); scroll(); }
    if (!what && typing) { typing.remove(); typing = null; }
  };

  // The voice note: spoken by the device in the reply's language; its words are under "Transcript".
  let playing = null;
  function voiceNote(text, locale) {
    const words = text.split(/\s+/).length;
    const secs = Math.max(2, Math.round(/[฀-໿က-႟ក-៿぀-鿿가-힯]/.test(text) ? text.length / 7 : words / 2.6));
    const time = el("span", { className: "wa-dur", textContent: `0:${String(secs).padStart(2, "0")}` });
    const bars = el("span", { className: "wa-wave" }, ...Array.from({ length: 28 }, (_, i) => el("i", { style: `height:${20 + Math.round(70 * Math.abs(Math.sin(i * 1.7 + text.length)))}%` })));
    const btn = el("button", { type: "button", className: "wa-play", "aria-label": "Play the voice note" }, svg(ICON.play));
    const note = el("small", { className: "wa-vnote" });
    const progress = (pct) => {
      bars.style.setProperty("--p", `${pct}%`);
      [...bars.children].forEach((b, i) => b.classList.toggle("played", (i + 0.5) / bars.children.length * 100 < pct));
    };
    const stop = () => { btn.replaceChildren(svg(ICON.play)); btn.setAttribute("aria-label", "Play the voice note"); progress(0); if (playing?.btn === btn) playing = null; };
    btn.onclick = () => {
      if (!("speechSynthesis" in window)) { note.textContent = "This browser can't play speech; the transcript is below."; return; }
      if (playing) { const was = playing.btn; speechSynthesis.cancel(); playing.stop(); if (was === btn) return; }
      const base = locale.split("-")[0].toLowerCase();
      const voices = speechSynthesis.getVoices();
      const voice = voices.find((v) => v.lang.replace("_", "-").toLowerCase() === locale.toLowerCase()) || voices.find((v) => v.lang.toLowerCase().startsWith(base));
      if (!voice && base !== "en" && voices.length) { note.textContent = "This device has no voice for this language. The words are in the transcript."; tr.open = true; return; }
      const u = new SpeechSynthesisUtterance(text);
      u.lang = locale;
      if (voice) u.voice = voice;
      u.rate = 0.95;
      const t0 = performance.now();
      const tick = () => { if (playing?.btn !== btn) return; progress(Math.min(100, (performance.now() - t0) / 10 / secs)); requestAnimationFrame(tick); };
      u.onend = u.onerror = stop;
      playing = { btn, stop };
      btn.replaceChildren(svg(ICON.pause));
      btn.setAttribute("aria-label", "Pause the voice note");
      speechSynthesis.speak(u);
      requestAnimationFrame(tick);
    };
    const tr = el("details", { className: "wa-tr" }, el("summary", { textContent: "Transcript" }), el("span", { textContent: text }));
    const b = bubble(false, el("div", { className: "wa-voice" }, btn, bars, el("span", { className: "wa-av mic" }, LOGO())), el("div", { className: "wa-vrow" }, time), note, tr);
    b.classList.add("voice");
  }

  // --- one message, as whatsapp/app.py handle() answers it ---
  async function handle(msg, mine) {
    const asked = parse(msg);
    lang = language(asked.text || asked.caption || "", lang);
    await wait(350);
    mine.querySelector(".wa-ticks").textContent = "✓✓";
    await wait(250);
    mine.querySelector(".wa-ticks").classList.add("read");
    steps.replaceChildren();
    step(`Message: ${asked.kind === "photo" ? "a photo" : asked.kind === "link" ? "a link" : asked.kind === "switch" ? "a language name" : "text"} · reply in ${LANGUAGES[lang][0]}`, "ok");
    setTyping("typing…");
    try {
      if (asked.kind === "help" || asked.kind === "switch") {
        const help = await fixed(lang, "help");
        setTyping(null);
        botText(help);
        return;
      }
      if (!takeQuota()) { setTyping(null); botText(usedUpText()); step("No checks left", "bad"); return; }
      const working = await fixed(lang, "working");
      setTyping(null);
      botText(working);
      setTyping("typing…");
      let identity, safety, trust = null, alts, text;
      if (asked.kind === "link") {
        const preset = presets.find((p) => p.request.listing.url === asked.url);
        let listing;
        if (preset) { listing = preset.request.listing; step(`Read the shop page (test page: ${preset.name})`, "ok"); } else {
          listing = await timed(`Read the shop page at ${new URL(asked.url).hostname}`, async () => {
            try { const read = await call("/v1/listings/read", { url: asked.url }); return { url: read.url || asked.url, ...read }; } catch (err) {
              if (err.status === 404 || err.status >= 500 || err.name === "TimeoutError") return { url: asked.url };
              throw err;
            }
          }).catch(() => ({ url: asked.url }));
        }
        identity = await timed("Which product is it? · POST /v1/products/identify", () => call("/v1/products/identify", listing));
        if (!identity.brand && !identity.model && !listing.title) { setTyping(null); botText(await fixed(lang, "unknown")); return; }
        [safety, trust, alts] = await Promise.all([
          timed(`Is it safe? · GET /safety (${productName(identity)})`, () => call(`/v1/products/${encodeURIComponent(identity.product_id)}/safety`)),
          timed("Is it real? · POST /v1/listings/trust-check", () => call("/v1/listings/trust-check", listing)),
          timed("Safer options · GET /alternatives", () => call(`/v1/products/${encodeURIComponent(identity.product_id)}/alternatives`))]);
        text = reply(identity, safety, lang, { trust, alternatives: alts });
      } else {
        const read = await timed("Read the label · POST /v1/camera/label (Gemini)", () => call("/v1/camera/label", { image: asked.image }, 90000));
        const seen = read.read || {};
        if (!seen.is_product_label || !(seen.brand || seen.model)) { setTyping(null); botText(await fixed(lang, "unknown")); return; }
        const listing = Object.fromEntries(Object.entries({ brand: seen.brand, model: seen.model, title: [seen.brand, seen.model].filter(Boolean).join(" "),
          certifications_claimed: seen.marks, label_text: [seen.brand, seen.model, seen.ratings, seen.batch && `Batch ${seen.batch}`, ...(seen.marks || [])].filter(Boolean).join("\n") }).filter(([, v]) => v && v.length !== 0));
        identity = await timed("Which product is it? · POST /v1/products/identify", () => call("/v1/products/identify", listing));
        [safety, alts] = await Promise.all([
          timed(`Is it safe? · GET /safety (${productName(identity)})`, () => call(`/v1/products/${encodeURIComponent(identity.product_id)}/safety`)),
          timed("Safer options · GET /alternatives", () => call(`/v1/products/${encodeURIComponent(identity.product_id)}/alternatives`))]);
        text = reply(identity, safety, lang, { alternatives: alts, fromPhoto: true });
      }
      step(`Answer set by code: ${safety.verdict}${safety.basis ? ` (${safety.basis.replace(/_/g, " ")})` : ""}`, "ok");
      // the voice note is the short spoken verdict (plain.say) in the shopper's language; otherwise the whole reply
      let spoken = null;
      const plain = safety.plain || {};
      if (plain.say) {
        spoken = lang === "en" ? { text: plain.say, speech_locale: "en-IN" }
          : await timed(`Voice note in ${LANGUAGES[lang][0]} · POST /v1/voice/verdict`, () => call("/v1/voice/verdict", { plain, language: lang }, 30000)).catch(() => null);
      }
      const said = TEXT[lang] ? text : await timed(`Translate the reply into ${LANGUAGES[lang][0]}`, () => translate(text, lang));
      setTyping(null);
      botText(said);
      setTyping("recording audio…");
      await wait(900);
      setTyping(null);
      if (spoken) voiceNote(voiceText(spoken.text), spoken.speech_locale || localeOf(lang));
      else voiceNote(voiceText(said), localeOf(said !== text || TEXT[lang] ? lang : "en"));
    } catch (err) {
      step(`Couldn't finish: ${err.message}`, "bad");
      setTyping(null);
      botText(await fixed(lang, "unknown").catch(() => TEXT.en.unknown)); // the shopper always gets an answer
    }
  }

  // one message at a time, like a chat
  let queue = Promise.resolve();
  function send(msg) {
    const mine = msg.type === "image"
      ? bubble(true, el("img", { className: "wa-img", src: msg.image, alt: "Your photo" }), ...(msg.caption ? [richText(msg.caption)] : []))
      : bubble(true, richText(msg.text));
    queue = queue.then(() => handle(msg, mine));
  }

  const sync = () => { sendBtn.replaceChildren(svg(input.value.trim() ? ICON.send : ICON.mic)); input.style.height = "auto"; input.style.height = `${Math.min(input.scrollHeight, 110)}px`; };
  input.addEventListener("input", sync);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
  form.onsubmit = (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) { input.focus(); input.placeholder = "Type a message, or send a photo"; return; }
    input.value = "";
    sync();
    send({ type: "text", text });
  };
  for (const pick of [photo, camera]) pick.onchange = async () => {
    const file = pick.files[0];
    pick.value = "";
    if (!file) return;
    try { send({ type: "image", image: await shrink(file), caption: input.value.trim() }); input.value = ""; sync(); } catch (_) { botText("I couldn't open that photo. Try a JPEG or PNG."); }
  };
  setInterval(() => { status.firstChild.textContent = clock(); }, 30000);
}
