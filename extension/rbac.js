// Firebase sign-in tokens authorize Firestore reads; local session roles never grant access.
import { API_BASE } from './config.js';
import { idToken } from './session.js';

const PROJECT_ID = 'shelf2026-3656b';

export async function identity() {
  const token = await idToken();
  const { session } = await chrome.storage.local.get('session');
  if (!session?.uid) throw new Error('Sign in again to verify your role.');
  const response = await fetch(`https://firestore.googleapis.com/v1/projects/${PROJECT_ID}/databases/(default)/documents/user_roles/${encodeURIComponent(session.uid)}`, {
    headers: { Authorization: `Bearer ${token}` }, signal: AbortSignal.timeout(15000),
  });
  if (response.status === 401) throw new Error('Sign in again to verify your role.');
  if (response.status === 403) throw new Error('Role access denied. Publish the updated Firestore rules.');
  if (response.status === 404) {
    // A missing role document means regular user. A missing database/configuration is an error.
    const error = await response.json();
    if (error.error?.message?.includes('Document') && error.error.message.includes('not found')) return { uid: session.uid, role: 'user' };
    throw new Error('Role document or Firestore database not found. Check Firebase setup.');
  }
  if (!response.ok) throw new Error('Could not verify Firebase permissions. Try again.');
  const document = await response.json();
  return { uid: session.uid, role: document.fields?.role?.stringValue === 'admin' ? 'admin' : 'user' };
}

export async function requireAdmin() {
  const who = await identity();
  if (who.role !== 'admin') throw new Error('Administrator access required');
  return who;
}

export async function adminStatus() {
  await requireAdmin();
  const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error('API status unavailable.');
  return response.json();
}
