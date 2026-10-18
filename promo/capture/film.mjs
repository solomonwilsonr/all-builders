// Films the real SafeShelf extension on the Amazon-layout page, through stub-api.mjs (start it first), and saves the
// stills the reel is cut from: promo/capture/shots/*.png at 2x, plus the widget card on its own.
//   node stub-api.mjs --delay 2500 &  node film.mjs [--port 8787]
import { chromium } from "../node_modules/playwright/index.mjs";
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, "shots");
mkdirSync(out, { recursive: true });
const port = process.argv.includes("--port") ? process.argv[process.argv.indexOf("--port") + 1] : "8787";

const browser = await chromium.launch();
// 1440×810 is the browser window's page area in the reel (the window chrome is drawn around it)
const page = await browser.newPage({ viewport: { width: 1440, height: 810 }, deviceScaleFactor: 2 });
page.on("pageerror", (e) => console.log("page error:", e.message));
await page.goto(`http://localhost:${port}/amazon.html`);
await page.waitForFunction(() => window.__safeshelfReady);
await page.waitForTimeout(1200);
const shot = (name) => page.screenshot({ path: join(out, `${name}.png`) });
const rail = page.locator(".float");
const shield = page.locator(".float button[aria-label*='Check' i], .float button[title*='Check' i]").first();

await page.mouse.move(700, 500);
await shot("01-page");
console.log("rail box", JSON.stringify(await rail.boundingBox()), "shield box", JSON.stringify(await shield.boundingBox()));
await shield.hover();
await page.waitForTimeout(500);
await shot("02-hover");
await shield.click();
await page.waitForTimeout(700);
await shot("03-checking");
// the answer: wait until the card shows a verdict word
await page.waitForFunction(() => /Don.t buy|Be careful|Looks fine|Not enough/.test(document.querySelector(".float").shadowRoot.querySelector(".box:not([hidden]) .card")?.innerText || ""), null, { timeout: 60000 });
// then until every follow-up check has answered
await page.waitForFunction(() => !/Checking|still checking/.test(document.querySelector(".float").shadowRoot.querySelector(".box:not([hidden]) .card")?.innerText || ""), null, { timeout: 90000 });
await page.waitForTimeout(800);
await page.mouse.move(700, 500);
await page.waitForTimeout(400);
await shot("04-result");
const card = page.locator(".float .box:not([hidden]) .card").first();
console.log("card box", JSON.stringify(await card.boundingBox()));
// the card is taller than the window and only its visible part is painted, so it is shot in a tall window
await page.setViewportSize({ width: 1440, height: 1900 });
await page.waitForTimeout(900);
await card.screenshot({ path: join(out, "05-card.png") });
await page.setViewportSize({ width: 1440, height: 810 });
await page.waitForTimeout(600);
// the whole card, unclipped, for the scroll-through shot
const full = await card.evaluate((el) => {
  const scroller = [el, ...el.querySelectorAll("*")].find((n) => n.scrollHeight > n.clientHeight + 4 && getComputedStyle(n).overflowY !== "visible");
  return scroller ? { h: scroller.scrollHeight, c: scroller.clientHeight } : null;
});
console.log("card scroll", JSON.stringify(full));
console.log("card text:", (await card.innerText()).slice(0, 600).replace(/\n+/g, " | "));
// the chat, for the languages shot
await page.locator(".float button[aria-label='Ask SafeShelf']").first().click();
await page.waitForTimeout(1200);
await page.mouse.move(700, 500);
await shot("06-chat");
const chat = page.locator(".float .box.chat:not([hidden]) .card, .float .box:not([hidden]) .card").first();
console.log("chat box", JSON.stringify(await chat.boundingBox()));
await chat.screenshot({ path: join(out, "07-chat-card.png") });
await browser.close();
const misses = await (await fetch(`http://localhost:${port}/_misses`)).json();
if (misses.length) {
  console.error(`These calls had no recorded answer, so the stills show mock data: ${misses.join(", ")}\nRecord them: node stub-api.mjs --record, then film again.`);
  process.exit(1);
}
