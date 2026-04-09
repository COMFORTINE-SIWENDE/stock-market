import { AppState } from './state.js';
import { logout } from './auth.js';
import { formatDate } from './utils.js';

export function cleanup() {}

export function init() {
  const token = AppState.token || localStorage.getItem('mm_token');

  if (token) {
    try {
      // Decode JWT payload (base64url decode middle segment)
      const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));

      const usernameEl = document.getElementById('profile-username');
      const emailEl = document.getElementById('profile-email');
      const createdEl = document.getElementById('profile-created');
      const avatarEl = document.getElementById('profile-avatar');

      if (usernameEl) usernameEl.textContent = payload.username || payload.sub || '—';
      if (emailEl) emailEl.textContent = payload.email || '—';
      if (createdEl) {
        const created = payload.created_at || payload.iat;
        if (created) {
          const date = typeof created === 'number'
            ? new Date(created * 1000).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
            : formatDate(created.slice(0, 10));
          createdEl.textContent = `Member since ${date}`;
        }
      }
      if (avatarEl) {
        const name = payload.username || payload.sub || '?';
        avatarEl.textContent = name.slice(0, 2).toUpperCase();
      }
    } catch {
      // JWT decode failed — show defaults
    }
  }

  // Wire logout button
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => logout());
  }
}
