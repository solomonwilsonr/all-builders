// SafeShelf site: the phone menu and the copy buttons. Nothing else runs on the page.
(() => {
  const nav = document.querySelector(".nav");
  const menu = document.querySelector(".menu");
  if (nav && menu) menu.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    menu.setAttribute("aria-expanded", String(open));
  });

  document.querySelectorAll("[data-copy-from]").forEach((b) => b.addEventListener("click", async () => {
    const src = document.getElementById(b.dataset.copyFrom);
    const label = b.textContent;
    try { await navigator.clipboard.writeText(src.innerText); b.textContent = "Copied"; }
    catch (_) { b.textContent = "Select and copy"; }
    setTimeout(() => { b.textContent = label; }, 1600);
  }));
})();
