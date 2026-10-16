import assert from "node:assert/strict";
import { buildConfig } from "../build-config.mjs";

const env = { EXTENSION_API_BASE: "http://localhost:8080/", EXTENSION_SHELF_SYNC: "false",
  EXTENSION_SIGNIN_URL: "http://localhost:8095/signin.html", EXTENSION_FIREBASE_API_KEY: "public-test-key",
  GOOGLE_API_KEY: "private-never-bundle", DB_PASSWORD: "private-password" };
const output = buildConfig(env);
assert.ok(output.includes('API_BASE = "http://localhost:8080"'));
assert.ok(output.includes("SHELF_SYNC = false"));
assert.ok(!output.includes("private") && !output.includes("GOOGLE_API_KEY") && !output.includes("DB_PASSWORD"));
assert.throws(() => buildConfig({ ...env, EXTENSION_API_BASE: "" }), /Missing EXTENSION_API_BASE/);
assert.throws(() => buildConfig({ ...env, EXTENSION_SHELF_SYNC: "no" }), /must be true or false/);
assert.throws(() => buildConfig({ ...env, EXTENSION_SIGNIN_URL: "javascript:alert(1)" }), /HTTP/);
const config = await import(`data:text/javascript,${encodeURIComponent(output)}`);
assert.equal(config.SHELF_SYNC, false);
assert.equal(config.FIREBASE_API_KEY, "public-test-key");
console.log("ok config: env validation, public settings only, valid generated module");
