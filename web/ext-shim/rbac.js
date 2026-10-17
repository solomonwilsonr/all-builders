// Roles for the extension inside the judges' page: the person signed in on the page. Admin-only tools stay closed.
import { API_BASE } from "./config.js";
import { account } from "./session.js";
export async function identity() { const who = await account(); return { uid: who?.email || "web", role: who?.role === "admin" ? "admin" : "user" }; }
export async function requireAdmin() { const who = await identity(); if (who.role !== "admin") throw new Error("Administrator access required"); return who; }
export async function adminStatus() { await requireAdmin(); return (await fetch(`${API_BASE}/health`)).json(); }
