import { api } from './api.js';
import { AppState } from './state.js';
import { showToast, formatPrice, formatDate, colorClass } from './utils.js';
import { createScatterChart, destroyChart } from './charts.js';

export function cleanup() {
  destroyChart('scatter-chart');
}

export async function init() {
  const symbol = AppState.currentSymbol;

  const [predsRes, backtestRes] = await Promise.allSettled([
    api.predictions.get(symbol, 7),
    api.predictions.backtest(symbol),
  ]);

  // Render backtest card
  if (backtestRes.status === 'fulfilled') {
    const bt = backtestRes.value;
    const mae = document.getElementById('bt-mae');
    const rmse = document.getElementById('bt-rmse');
    const count = document.getElementById('bt-count');
    if (mae) mae.textContent = bt.mae != null ? `$${bt.mae.toFixed(2)}` : '—';
    if (rmse) rmse.textContent = bt.rmse != null ? `$${bt.rmse.toFixed(2)}` : '—';
    if (count) count.textContent = bt.count ?? '—';
  } else {
    showToast(backtestRes.reason?.message || 'Failed to load backtest', 'error');
  }

  // Render predictions table and scatter chart
  if (predsRes.status === 'fulfilled') {
    const preds = predsRes.value.predictions || [];
    renderPredictionsTable(preds);
    renderScatterChart(preds);
  } else {
    showToast(predsRes.reason?.message || 'Failed to load predictions', 'error');
  }

  // Wire train button
  const trainBtn = document.getElementById('train-btn');
  if (trainBtn) {
    trainBtn.addEventListener('click', async () => {
      const spinner = document.getElementById('train-spinner');
      const icon = document.getElementById('train-icon');
      trainBtn.classList.add('btn-loading');
      if (spinner) spinner.style.display = 'inline-block';
      if (icon) icon.style.display = 'none';
      try {
        const res = await api.predictions.train(symbol);
        showToast(`Model trained — MSE: ${res.mse?.toFixed(6) ?? '?'}, MAE: ${res.mae?.toFixed(6) ?? '?'}`, 'success');
        await init(); // refresh
      } catch (err) {
        showToast(err.message || 'Training failed', 'error');
      } finally {
        trainBtn.classList.remove('btn-loading');
        if (spinner) spinner.style.display = 'none';
        if (icon) icon.style.display = '';
      }
    }, { once: true });
  }
}

function renderPredictionsTable(preds) {
  const container = document.getElementById('predictions-table');
  if (!container) return;
  if (preds.length === 0) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-brain"></i><p>No predictions available</p></div>';
    return;
  }
  const rows = preds.map(p => {
    const trendClass = p.trend_direction === 'up' ? 'positive' : 'negative';
    const trendIcon = p.trend_direction === 'up' ? '▲' : '▼';
    const confPct = (p.confidence_score * 100).toFixed(0);
    return `<tr>
      <td>${formatDate(p.target_date)}</td>
      <td>${formatPrice(p.predicted_price)}</td>
      <td><span class="${trendClass}">${trendIcon} ${p.trend_direction}</span></td>
      <td>
        <div style="display:flex;align-items:center;gap:8px;">
          <div class="confidence-bar" style="width:60px;"><div class="confidence-fill" style="width:${confPct}%"></div></div>
          <span>${confPct}%</span>
        </div>
      </td>
      <td><span class="badge">${p.model_source}</span></td>
    </tr>`;
  }).join('');
  container.innerHTML = `<table>
    <thead><tr><th>Date</th><th>Predicted Price</th><th>Trend</th><th>Confidence</th><th>Model</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function renderScatterChart(preds) {
  const points = preds.map(p => ({ x: p.confidence_score, y: p.predicted_price }));
  createScatterChart('scatter-chart', [{
    label: 'Predictions',
    data: points,
    backgroundColor: '#6366f1',
    pointRadius: 6,
  }]);
}
