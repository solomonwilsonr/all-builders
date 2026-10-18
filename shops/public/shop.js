// The test shops' small bits of life: photo thumbnails, a note that nothing is for sale, and MegaDealz24's fake countdown.
const toast = (text) => {
  let t = document.querySelector(".toast");
  if (!t) { t = Object.assign(document.createElement("div"), { className: "toast", role: "status" }); document.body.append(t); }
  t.textContent = text;
  t.classList.add("on");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove("on"), 2600);
};

document.querySelectorAll("[data-show]").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".shot").forEach((s) => s.classList.toggle("on", s.dataset.shot === b.dataset.show));
  document.querySelectorAll(".thumb").forEach((t) => t.classList.toggle("on", t === b));
}));

document.querySelectorAll("button[data-demo]").forEach((b) => b.addEventListener("click", () =>
  toast("This is a SafeShelf test shop: nothing is for sale. Press Check on the right edge instead.")));
// the classic fake-shop pressure timer: it restarts on every visit
const clock = document.querySelector("[data-countdown]");
if (clock) {
  let left = 599;
  setInterval(() => {
    left = left > 0 ? left - 1 : 599;
    clock.textContent = `00:${String(Math.floor(left / 60)).padStart(2, "0")}:${String(left % 60).padStart(2, "0")}`;
  }, 1000);
}
