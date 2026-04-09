// ── 4.1 Toast Notifications ─────────────────────────────────────────────────

const ICON_MAP = {
  success: 'fa-check-circle',
  error: 'fa-circle-xmark',
  info: 'fa-circle-info',
  warning: 'fa-triangle-exclamation',
};

const DEFAULT_DURATION = {
  success: 3000,
  info: 3000,
  warning: 4000,
  error: 5000,
};

export function showToast(message, type = 'info', duration) {
  const ms = duration ?? DEFAULT_DURATION[type] ?? 3000;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icon = document.createElement('i');
  icon.className = `fa-solid ${ICON_MAP[type] ?? 'fa-circle-info'}`;
  toast.appendChild(icon);

  const text = document.createElement('span');
  text.textContent = message;
  toast.appendChild(text);

  const dismiss = () => {
    toast.classList.add('dismissing');
    setTimeout(() => toast.remove(), 300);
  };

  toast.addEventListener('click', dismiss);

  document.getElementById('toast-container')?.appendChild(toast);

  setTimeout(dismiss, ms);
}

// ── 4.2 Skeleton Helpers ─────────────────────────────────────────────────────

export function showSkeleton(containerId, rows = 3) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  for (let i = 0; i < rows; i++) {
    const row = document.createElement('div');
    row.className = 'skeleton skeleton-row';
    container.appendChild(row);
  }
}

export function hideSkeleton(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.querySelectorAll('.skeleton-row').forEach(el => el.remove());
}

// ── 4.3 Date and Number Helpers ──────────────────────────────────────────────

export function formatDate(dateStr) {
  const [year, month, day] = dateStr.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export function today() {
  return new Date().toISOString().slice(0, 10);
}

export function formatPrice(n) {
  return '$' + n.toFixed(2);
}

export function formatPercent(n) {
  const sign = n >= 0 ? '+' : '';
  return `${sign}${n.toFixed(2)}%`;
}

export function colorClass(n) {
  if (n > 0.1) return 'positive';
  if (n < -0.1) return 'negative';
  return 'neutral';
}
