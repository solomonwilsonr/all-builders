// SafeShelf social impact demo (impact.html): the same sign-in and check limit as the judges' page (auth.js, quota.js),
// with the WhatsApp chat (whatsapp.js) as the one live tool, first on the page. Everything else is static text.
import { quota, requireSignIn } from "./auth.js?v=20261018u";
import { setUpWhatsApp } from "./whatsapp.js?v=20261018c";

// --- The site's top bar: the phone menu, and the bar's border once the page scrolls (as in app.js) ---
function setUpTopBar() {
  const top = document.querySelector("body > header.top");
  const menu = top?.querySelector(".menu");
  if (!top) return;
  menu?.addEventListener("click", () => menu.setAttribute("aria-expanded", String(top.classList.toggle("open"))));
  top.querySelectorAll(".links a").forEach((a) => a.addEventListener("click", () => { top.classList.remove("open"); menu?.setAttribute("aria-expanded", "false"); }));
  const onScroll = () => top.classList.toggle("scrolled", scrollY > 8);
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}

// --- The jump bar marks the section on screen ---
function setUpJump() {
  const links = [...document.querySelectorAll(".jump a")];
  const seen = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      links.forEach((a) => a.toggleAttribute("aria-current", a.hash === `#${e.target.id}`));
    }
  }, { rootMargin: "-40% 0px -55% 0px" });
  links.forEach((a) => { const s = document.querySelector(a.hash); if (s) seen.observe(s); });
}

await requireSignIn();
setUpTopBar();
setUpJump();
const takeQuota = () => { if (!quota.left()) return false; quota.take().catch(() => {}); return true; };
setUpWhatsApp(takeQuota, () => quota.usedUpText());
