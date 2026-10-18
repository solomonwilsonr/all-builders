// Captures the live homepage's own sections (web/site/index.html) at 2x for reel-site-40s.html, so the film's later
// scenes are the website itself. Animations settle first (reduced motion); the Help button and sticky nav are hidden.
//   node capture/site-sections.mjs [url]
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const out = resolve(here, "site2");
mkdirSync(out, { recursive: true });
const url = process.argv[2] || "https://shelf2026-3656b.web.app/site/index.html";
const SHOTS = {
  hero: ".h-hero", logos: ".h-logos", bento: ".bento", ask: ".ask", agent: ".h-sec.agent",
  plans: ".plans", recs: "section[aria-labelledby='rec-h']", cta: ".h-cta",
};
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2, reducedMotion: "reduce" });
await page.goto(url, { waitUntil: "networkidle" });
await page.addStyleTag({ content: ".top, [class^='sup-'], [class*=' sup-'] { visibility: hidden !important; }" });
for (const [name, sel] of Object.entries(SHOTS)) {
  const el = page.locator(sel).first();
  await el.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1200);
  await el.screenshot({ path: resolve(out, `${name}.png`) });
  if (name === "logos") {  // without the hero chat box's shadow along the top edge (the reel uses logos-crop.png)
    const b = await el.boundingBox();
    await page.screenshot({ path: resolve(out, "logos-crop.png"), clip: { x: b.x, y: b.y + 60, width: b.width, height: b.height - 60 } });
  }
  console.log(name, await el.boundingBox().then((b) => `${Math.round(b.width)}x${Math.round(b.height)}`));
}
const cells = page.locator(".bento .cell");
for (let i = 0; i < await cells.count(); i++) {
  await cells.nth(i).scrollIntoViewIfNeeded();
  await page.waitForTimeout(500);
  await cells.nth(i).screenshot({ path: resolve(out, `cell${i}.png`) });
}
await browser.close();
