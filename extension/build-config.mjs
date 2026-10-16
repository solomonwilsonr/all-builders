import { readFileSync, writeFileSync } from "node:fs";
import { parseEnv } from "node:util";
import { pathToFileURL } from "node:url";

// Only public extension settings are copied; server/Gemini secrets stay in .env.
export function buildConfig(env) {
  const required = (key) => {
    const value = env[key]?.trim();
    if (!value) throw new Error(`Missing ${key} in root .env`);
    return value;
  };
  const api = required("EXTENSION_API_BASE");
  const signin = required("EXTENSION_SIGNIN_URL");
  for (const [key, value] of [["EXTENSION_API_BASE", api], ["EXTENSION_SIGNIN_URL", signin]]) {
    let url;
    try { url = new URL(value); } catch { throw new Error(`${key} must be an HTTP(S) URL`); }
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) throw new Error(`${key} must be an HTTP(S) URL without credentials`);
  }
  const sync = required("EXTENSION_SHELF_SYNC");
  if (!["true", "false"].includes(sync)) throw new Error("EXTENSION_SHELF_SYNC must be true or false");
  const values = { API_BASE: api.replace(/\/$/, ""), SHELF_SYNC: sync === "true", SIGNIN_URL: signin,
    FIREBASE_API_KEY: required("EXTENSION_FIREBASE_API_KEY") };
  return "// Generated public settings from root .env; do not edit.\n" +
    Object.entries(values).map(([key, value]) => `export const ${key} = ${JSON.stringify(value)};`).join("\n") + "\n";
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const env = parseEnv(readFileSync(new URL("../.env", import.meta.url), "utf8"));
  writeFileSync(new URL("./config.generated.js", import.meta.url), buildConfig(env));
  console.log("Generated extension configuration from root .env");
}
