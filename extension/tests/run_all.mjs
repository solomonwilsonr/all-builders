// node extension/tests/run_all.mjs : runs every extension test and fails if any does.
import { readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
const dir = fileURLToPath(new URL(".", import.meta.url)); // decodes spaces in the folder name
let failed = 0;
for (const f of readdirSync(dir).filter((f) => /\.test\.(cjs|mjs)$/.test(f)).sort()) {
  const r = spawnSync("node", [dir + f], { encoding: "utf8" });
  process.stdout.write(r.status === 0 ? r.stdout : `FAIL ${f}\n${r.stdout}${r.stderr}\n`);
  if (r.status !== 0) failed++;
}
process.exit(failed ? 1 : 0);
