import { AppState } from './state.js';
import { api } from './api.js';

// ── Route definitions ────────────────────────────────────────────────────────

const ROUTES = {
  '/dashboard':   { page: 'pages/dashboard.html',   module: () => import('./dashboard.js'),   auth: true },
  '/predictions': { page: 'pages/predictions.html', module: () => import('./predictions.js'), auth: true },
  '/sentiment':   { page: 'pages/sentiment.html',   module: () => import('./sentiment.js'),   auth: true },
  '/stocks':      { page: 'pages/stocks.html',       module: () => import('./stocks.js'),       auth: true },
  '/history':     { page: 'pages/history.html',      module: () => import('./history.js'),      auth: true },
  '/profile':     { page: 'pages/profile.html',      module: () => import('./profile.js'),      auth: true },
  '/login':       { page: 'pages/login.html',        module: () => import('./auth.js'),         auth: false },
  '/register':    { page: 'pages/register.html',     module: () => import('./auth.js'),         auth: false },
};

// Tracks the currently active page module so we can call cleanup() on navigation
let currentModule = null;

// ── Router ───────────────────────────────────────────────────────────────────

export async function navigate(hash) {
  const routeKey = hash.replace(/^#/, '') || '/dashboard';
  const route = ROUTES[routeKey];

  // Auth guard
  if (!route) {
    window.location.hash = AppState.token ? '#/dashboard' : '#/login';
    return;
  }

  if (route.auth && !AppState.token) {
    window.location.hash = '#/login';
    return;
  }

  if (!route.auth && AppState.token && (routeKey === '/login' || routeKey === '/register')) {
    window.location.hash = '#/dashboard';
    return;
  }

  // Cleanup previous module
  if (currentModule && typeof currentModule.cleanup === 'function') {
    currentModule.cleanup();
  }
  currentModule = null;

  // Fetch and inject page HTML fragment
  try {
    const res = await fetch(route.page);
    const html = await res.text();
    const appContent = document.getElementById('app-content');
    if (appContent) {
      appContent.innerHTML = html;
    }
  } catch {
    // If fetch fails, leave content as-is
  }

  // Dynamically import the page module and call the appropriate init
  try {
    const mod = await route.module();
    currentModule = mod;

    if (routeKey === '/login' && typeof mod.initLogin === 'function') {
      mod.initLogin();
    } else if (routeKey === '/register' && typeof mod.initRegister === 'function') {
      mod.initRegister();
    } else if (typeof mod.init === 'function') {
      mod.init();
    }
  } catch {
    // Module load failure — leave page content as-is
  }

  // Update active route in state
  AppState.activeRoute = routeKey;

  // Update sidebar active class
  document.querySelectorAll('.nav-link[data-route]').forEach(link => {
    if (link.dataset.route === routeKey) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Show/hide sidebar based on auth state
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    const isAuthPage = routeKey === '/login' || routeKey === '/register';
    sidebar.style.display = isAuthPage ? 'none' : '';
  }
}

export function getCurrentRoute() {
  return AppState.activeRoute;
}

// ── Symbol search ────────────────────────────────────────────────────────────

function initSymbolSearch() {
  const input = document.getElementById('symbol-search');
  const dropdown = document.getElementById('search-dropdown');
  if (!input || !dropdown) return;

  let debounceTimer = null;
  let previousSymbol = AppState.currentSymbol;
  let isSelecting = false;

  // Set initial input value
  input.value = AppState.currentSymbol;

  function closeDropdown() {
    dropdown.classList.remove('open');
    dropdown.innerHTML = '';
  }

  function renderResults(results) {
    dropdown.innerHTML = '';
    if (!results || results.length === 0) {
      const noResults = document.createElement('div');
      noResults.className = 'search-no-results';
      noResults.textContent = 'No symbols found';
      dropdown.appendChild(noResults);
    } else {
      results.forEach(({ symbol, company_name }) => {
        const item = document.createElement('div');
        item.className = 'search-item';

        const bold = document.createElement('strong');
        bold.textContent = symbol;
        item.appendChild(bold);

        if (company_name) {
          const name = document.createElement('span');
          name.textContent = ` ${company_name}`;
          item.appendChild(name);
        }

        item.addEventListener('mousedown', () => {
          isSelecting = true;
        });

        item.addEventListener('click', () => {
          previousSymbol = symbol;
          AppState.setSymbol(symbol);
          input.value = symbol;
          closeDropdown();
          isSelecting = false;
          navigate(`#${getCurrentRoute()}`);
        });

        dropdown.appendChild(item);
      });
    }
    dropdown.classList.add('open');
  }

  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (q.length < 2) {
      closeDropdown();
      return;
    }
    debounceTimer = setTimeout(async () => {
      try {
        const results = await api.symbols.search(q);
        renderResults(results);
      } catch {
        closeDropdown();
      }
    }, 300);
  });

  input.addEventListener('focus', () => {
    const q = input.value.trim();
    if (q.length >= 2 && dropdown.children.length > 0) {
      dropdown.classList.add('open');
    }
  });

  input.addEventListener('blur', () => {
    if (isSelecting) return;
    closeDropdown();
    input.value = previousSymbol;
  });
}

// ── Hamburger toggle ─────────────────────────────────────────────────────────

function initHamburger() {
  const btn = document.getElementById('hamburger-btn');
  const sidebar = document.getElementById('sidebar');
  if (!btn || !sidebar) return;

  btn.addEventListener('click', () => {
    sidebar.classList.toggle('drawer-open');
  });

  document.addEventListener('click', (e) => {
    if (
      sidebar.classList.contains('drawer-open') &&
      !sidebar.contains(e.target) &&
      e.target !== btn &&
      !btn.contains(e.target)
    ) {
      sidebar.classList.remove('drawer-open');
    }
  });
}

// ── Bootstrap ────────────────────────────────────────────────────────────────

window.addEventListener('hashchange', () => {
  navigate(window.location.hash || '#/dashboard');
});

window.addEventListener('DOMContentLoaded', () => {
  navigate(window.location.hash || '#/dashboard');
  initSymbolSearch();
  initHamburger();
});
