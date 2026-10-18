// Renders demo-30s.html to an MP4: headless Chromium seeks the animation one frame at a time and pipes each
// screenshot into ffmpeg, so the video is smooth however slow the machine is.
//   node render.mjs [--page demo-30s.html] [--fps 30] [--scale 1] [--from 0] [--to 30] [--out out/<page>.mp4]
// --page apple-30s.html renders the keynote-style cut. --speed 1.25 plays it 1.25× faster (every frame still rendered).
// --scale 2 renders 3840×2160. --from/--to render part of it while you tweak a scene.
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const arg = (name, fallback) => {
  const i = process.argv.indexOf(`--${name}`);
  return i > 0 ? process.argv[i + 1] : fallback;
};
const fps = Number(arg("fps", 30));
const scale = Number(arg("scale", 1));
const speed = Number(arg("speed", 1));
const pageFile = arg("page", "demo-30s.html");
const out = resolve(here, arg("out", `out/safeshelf-${pageFile.replace(/\.html$/, "")}.mp4`));
mkdirSync(dirname(out), { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
await page.goto(`${pathToFileURL(resolve(here, pageFile))}?render=1`, { waitUntil: "networkidle" });
await page.evaluate(() => window.ready);
const duration = await page.evaluate(() => window.DURATION);
const from = Number(arg("from", 0)), to = Math.min(Number(arg("to", duration)), duration);
const frames = Math.round(((to - from) * fps) / speed);

const ffmpeg = spawn("ffmpeg", [
  "-y", "-loglevel", "error",
  "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
  "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
  out,
], { stdio: ["pipe", "inherit", "inherit"] });
const done = new Promise((ok, fail) => ffmpeg.on("close", (code) => (code ? fail(new Error(`ffmpeg exited ${code}`)) : ok())));

for (let f = 0; f < frames; f++) {
  await page.evaluate((t) => window.seek(t), from + (f * speed) / fps);
  const png = await page.screenshot({ type: "png" });
  if (!ffmpeg.stdin.write(png)) await new Promise((ok) => ffmpeg.stdin.once("drain", ok));
  if (f % fps === 0) process.stdout.write(`\r${((f * speed) / fps + from).toFixed(0)}s / ${to}s`);
}
ffmpeg.stdin.end();
await done;
await browser.close();
console.log(`\r${out} (${frames} frames, ${fps} fps, ${1920 * scale}×${1080 * scale})`);
