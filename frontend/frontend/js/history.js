import { api } from './api.js';
import { AppState } from './state.js';
import { showToast, formatPrice, formatDate } from './utils.js';

let _historyData = [];
let _sortCol = 'prediction_date';
let _sortDir = 'desc';

export function cleanup() {
  _historyData = [];
}

export async function init() {
  const symbol = AppState.currentSymbol;

  const [historyRes, backtestRes] = await Promise.allSettled([
    api.predictions.history(symbol),
    api.predictions.backtest(symbol),
  ]);

  // Render backtest stats
  if (backtestRes.status === 'fulfilled') {
    const bt = backtestRes.value;
    const mae = document.getElementById('hist-mae');
    const rmse = document.getElementById('hist-rmse');
    const count = document.getElementById('hist-count');
    if (mae) mae.textContent = bt.mae != null ? `$${bt.mae.toFixed(2)}` : '—';
    if (rmse) rmse.textContent = bt.rmse != null ? `$${bt.rmse.toFixed(2)}` : '—';
    if (count) count.textContent = bt.count ?? '—';
  } else {
    showToast(backtestRes.reason?.message || 'Failed to load backtest', 'error');
  }

  // Render history table
  if (historyRes.status === 'fulfilled') {
    _historyData = historyRes.value.history || [];
    renderHistoryTable();
    wireColumnSorting();
  } else {
    showToast(historyRes.reason?.message || 'Failed to load history', 'error');
  }
}

function renderHistoryTable() {
  const tbody = document.getElementById('history-tbody');
  if (!tbody) return;

  if (_historyData.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#9ca3af;padding:24px;">No predictions yet</td></tr>';
    return;
  }

  // Sort
  const sorted = [..._historyData].sort((a, b) => {
    let aVal = a[_sortCol];
    let bVal = b[_sortCol];
    // Handle null actual_price for sorting
    if (aVal == null) aVal = _sortDir === 'asc' ? Infinity : -Infinity;
    if (bVal == null) bVal = _sortDir === 'asc' ? Infinity : -Infinity;
    if (typeof aVal === 'string') aVal = aVal.toLowerCase();
    if (typeof bVal === 'string') bVal = bVal.toLowerCase();
    if (aVal < bVal) return _sortDir === 'asc' ? -1 : 1;
    if (aVal > bVal) return _sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  tbody.innerHTML = sorted.map(h => {
    const error = h.actual_price != null
      ? ((h.actual_price - h.predicted_price) / h.predicted_price * 100).toFixed(2)
      : null;
    const errorHtml = error != null
      ? `<span class="${parseFloat(error) >= 0 ? 'positive' : 'negative'}">${parseFloat(error) >= 0 ? '+' : ''}${error}%</span>`
      : '—';
    const trendClass = h.trend_direction === 'up' ? 'positive' : 'negative';
    const confPct = h.confidence_score != null ? (h.confidence_score * 100).toFixed(0) + '%' : '—';
    return `<tr>
      <td>${formatDate(h.prediction_date)}</td>
      <td>${formatDate(h.target_date)}</td>
      <td>${formatPrice(h.predicted_price)}</td>
      <td>${h.actual_price != null ? formatPrice(h.actual_price) : '<span style="color:#9ca3af;">Pending</span>'}</td>
      <td>${errorHtml}</td>
      <td>${confPct}</td>
      <td><span class="${trendClass}">${h.trend_direction === 'up' ? '▲' : '▼'} ${h.trend_direction}</span></td>
      <td><span class="badge">${h.model_source}</span></td>
    </tr>`;
  }).join('');

  // Update sort indicators on headers
  document.querySelectorAll('#history-table th[data-col]').forEach(th => {
    const icon = th.querySelector('i');
    if (!icon) return;
    if (th.dataset.col === _sortCol) {
      icon.className = `fas fa-sort-${_sortDir === 'asc' ? 'up' : 'down'}`;
      icon.style.color = '#6366f1';
    } else {
      icon.className = 'fas fa-sort';
      icon.style.color = '#6366f1';
    }
  });
}

function wireColumnSorting() {
  document.querySelectorAll('#history-table th[data-col]').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      if (_sortCol === col) {
        _sortDir = _sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        _sortCol = col;
        _sortDir = 'asc';
      }
      renderHistoryTable();
    });
  });
}
