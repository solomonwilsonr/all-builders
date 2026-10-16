const ICON = { unknown: "Can't tell yet", green: "No problems found", amber: "Be careful", red: "Don't buy" };
const list = document.getElementById("list");
const empty = document.getElementById("empty");

const el = (tag, props = {}, ...kids) => {
  const n = Object.assign(document.createElement(tag), props);
  n.append(...kids);
  return n;
};

async function load() {
  const { shelf = [] } = await chrome.storage.local.get("shelf");
  return shelf;
}

async function render() {
  const shelf = await load();
  empty.hidden = shelf.length > 0;
  list.replaceChildren(
    ...shelf.map((item) => {
      const remove = el("button", { type: "button", textContent: "Remove" });
      remove.setAttribute("aria-label", `Remove ${item.title} from My Shelf`);
      remove.onclick = async () => {
        await chrome.storage.local.set({ shelf: (await load()).filter((i) => i.id !== item.id) });
        render();
      };
      const title = /^https?:/.test(item.url) ? el("a", { href: item.url, target: "_blank", rel: "noopener", textContent: item.title }) : el("span", { textContent: item.title });
      return el("li", { className: item.level || "" },
        el("div", { className: "row" }, title, remove),
        el("span", { className: "status", textContent: ICON[item.level] || "Not checked yet" }),
        el("span", { className: "meta", textContent: `${item.host} · saved ${new Date(item.saved_at).toLocaleString()}${item.next_check ? ` · next recall check ${new Date(item.next_check).toLocaleString()}` : ""}${item.synced ? " · saved to the API" : ""}` }),
      );
    }),
  );
}

chrome.storage.onChanged.addListener(render);
render();
