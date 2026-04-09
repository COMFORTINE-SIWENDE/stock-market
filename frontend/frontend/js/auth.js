import { api, ApiError } from './api.js';
import { AppState } from './state.js';
import { showToast } from './utils.js';

// Called by router when #/register page loads
export function initRegister() {
  const form = document.getElementById('register-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('[type="submit"]');
    btn.classList.add('btn-loading');
    try {
      const data = {
        email: form.email.value.trim(),
        username: form.username.value.trim(),
        full_name: form.full_name.value.trim(),
        password: form.password.value,
      };
      await api.auth.register(data);
      showToast('Account created! Please sign in.', 'success');
      window.location.hash = '#/login';
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'Registration failed', 'error');
    } finally {
      btn.classList.remove('btn-loading');
    }
  });
}

// Called by router when #/login page loads
export function initLogin() {
  const form = document.getElementById('login-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('[type="submit"]');
    btn.classList.add('btn-loading');
    try {
      const data = {
        username_or_email: form.username_or_email.value.trim(),
        password: form.password.value,
      };
      const res = await api.auth.login(data);
      AppState.setToken(res.token);
      window.location.hash = '#/dashboard';
    } catch (err) {
      AppState.setToken(null);
      showToast(
        err instanceof ApiError && err.status === 401
          ? 'Invalid credentials'
          : (err.message || 'Login failed'),
        'error'
      );
    } finally {
      btn.classList.remove('btn-loading');
    }
  });
}

export async function logout() {
  try {
    await api.auth.logout();
  } catch {
    // ignore logout API errors — always clear local state
  } finally {
    AppState.setToken(null);
    AppState.setUser(null);
    window.location.hash = '#/login';
  }
}

// No-op default init — router calls module.init() on every page load;
// auth-specific pages use initLogin/initRegister directly.
export default function init() {}
