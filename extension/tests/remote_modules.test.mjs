// The remote browser ("Start a real browser" on the judges' page) swaps in its own session.js and rbac.js
// (browser/remote/). Every name the extension imports from them must exist there, or Chrome refuses to load the
// background worker and no check runs.
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";

const ext = new URL("../", import.meta.url);
const remote = new URL("../../browser/remote/", import.meta.url);
const exported = (src) => new Set([...src.matchAll(/^export\s+(?:async\s+)?(?:function|const|let|class)\s+([A-Za-z_$][\w$]*)/gm)].map((m) => m[1]));

for (const mod of ["session.js", "rbac.js"]) {
  const have = exported(readFileSync(new URL(mod, remote), "utf8"));
  for (const f of readdirSync(ext).filter((f) => f.endsWith(".js"))) {
    const src = readFileSync(new URL(f, ext), "utf8");
    for (const m of src.matchAll(new RegExp(String.raw`import\s*\{([^}]*)\}\s*from\s*["']\./${mod.replace(".", "\\.")}["']`, "g"))) {
      for (const name of m[1].split(",").map((s) => s.trim().split(/\s+as\s+/)[0]).filter(Boolean)) {
        assert.ok(have.has(name), `${f} imports ${name} from ${mod}, but browser/remote/${mod} doesn't export it`);
      }
    }
  }
}
console.log("ok  remote browser: session.js and rbac.js export everything the extension imports");
