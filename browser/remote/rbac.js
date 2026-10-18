// Roles inside the remote browser: the judge, as a shopper. Admin-only tools stay closed.
import { API_BASE } from "./config.js";
import { account } from "./session.js";
export async function identity() { const who = await account(); return { uid: who?.email || "remote", role: "user" }; }
export async function requireAdmin() { throw new Error("Administrator access required"); }
export async function adminStatus() { await requireAdmin(); return (await fetch(`${API_BASE}/health`)).json(); }
