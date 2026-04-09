import { api, ApiError } from './api.js';
import { AppState } from './state.js';
import { showToast, showSkeleton, hideSkeleton, formatPrice, formatPercent, formatDate, daysAgo, today, colorClass } from './utils.js';
import { createLineChart, destroyChart } from './charts.js';

let _pollInterval = null;

export function cleanup() {
  if (_pollInterval) {
    clearInterval(_pollInterval);
    _pollInterval = null;
  }
  destroyChart('priceChart');
  destroyChart('sentimentChart');
}

export async function init() {
  const symbol = AppState.currentSymbol;

  // Update symbol badge
  const badge = document.getElementById('current-symbol-badge');
  if (badge) badge.textContent = symbol;
  const chartBadge = document.getElementById('chart-symbol-badge');
  if (chartBadge) chartBadge.textContent = symbol;

  // Show skeletons
  showSkeleton('price-card', 3);
  showSkeleton('prediction-card', 3);
  showSkeleton('sentiment-card', 2);
  showSkeleton('history-table', 4);

  // Load all data in parallel
  const [priceRes, predictionsRes, sentimentRes, stockDataRes, historyRes] = await Promise.allSettled([
    api.stocks.price(symbol),
    api.predictions.get(symbol, 5),
    api.sentiment.get(symbol),
    api.stocks.data(symbol, daysAgo(30), today()),
    api.predictions.history(symbol),
  ]);

  // Render price card
  hideSkeleton('price-card');
  if (priceRes.status === 'fulfilled') {
    renderPriceCard(priceRes.value);
  } else {
    showToast(priceRes.reason?.message || 'Failed to load price', 'error');
  }

  // Render prediction card
  hideSkeleton('prediction-card');
  if (predictionsRes.status === 'fulfilled') {
    renderPredictionCard(predictionsRes.value);
  } else {
    showToast(predictionsRes.reason?.message || 'Failed to load predictions', 'error');
  }

  // Render sentiment gauge
  if (sentimentRes.status === 'fulfilled') {
    renderSentimentGauge(sentimentRes.value);
    renderSentimentChart(sentimentRes.value);
  } else {
    showToast(sentimentRes.reason?.message || 'Failed to load sentiment', 'error');
  }

  // Render price chart
  if (stockDataRes.status === 'fulfilled' && predictionsRes.status === 'fulfilled') {
    renderPriceChart(stockDataRes.value, predictionsRes.value);
  }

  // Render history table
  hideSkeleton('history-table');
  if (historyRes.status === 'fulfilled') {
    renderHistoryTable(historyRes.value);
  } else {
    showToast(historyRes.reason?.message || 'Failed to load history', 'error');
  }

  // Start polling
  _pollInterval = setInterval(async () => {
    try {
      const res = await api.stocks.price(symbol);
      renderPriceCard(res);
    } catch (err) {
      // silent poll failure
    }
  }, 30000);

  // Wire agent chat
  initAgentChat();
}

function renderPriceCard(data) {
  // data = { symbol, price } from GET /stocks/{symbol}/price
  // For high/low/volume we use what's available; if not in response, show '—'
  const priceEl = document.getElementById('price-value');
  if (priceEl) priceEl.textContent = formatPrice(data.price);
  // high/low/volume not in /price endpoint — leave as '—' unless data has them
}

function renderPredictionCard(data) {
  // data = { symbol, predictions: [...] }
  const preds = data.predictions || [];
  const tomorrow = preds[0];
  const fiveDay = preds[preds.length - 1] || preds[0];

  const tomorrowEl = document.getElementById('pred-tomorrow');
  if (tomorrowEl && tomorrow) {
    tomorrowEl.querySelector('.value').textContent = formatPrice(tomorrow.predicted_price);
    const changeClass = tomorrow.trend_direction === 'up' ? 'positive' : 'negative';
    tomorrowEl.querySelector('.change').innerHTML = `<span class="${changeClass}">${tomorrow.trend_direction === 'up' ? '▲' : '▼'} ${(tomorrow.confidence_score * 100).toFixed(0)}% conf.</span>`;
  }

  const fiveDayEl = document.getElementById('pred-5day');
  if (fiveDayEl && fiveDay) {
    fiveDayEl.querySelector('.value').textContent = formatPrice(fiveDay.predicted_price);
    const changeClass = fiveDay.trend_direction === 'up' ? 'positive' : 'negative';
    fiveDayEl.querySelector('.change').innerHTML = `<span class="${changeClass}">${fiveDay.trend_direction === 'up' ? '▲' : '▼'}</span>`;
  }

  const confEl = document.getElementById('pred-confidence');
  if (confEl && tomorrow) confEl.textContent = `${(tomorrow.confidence_score * 100).toFixed(0)}%`;

  const trendBanner = document.getElementById('trend-banner');
  if (trendBanner && tomorrow) {
    const isUp = tomorrow.trend_direction === 'up';
    trendBanner.className = `trend-banner${isUp ? '' : ' bearish'}`;
    trendBanner.innerHTML = `<i class="fas fa-chart-line"></i> Trend: <strong class="gradient-text">${isUp ? 'Uptrend' : 'Downtrend'}</strong>`;
  }
}

function renderSentimentGauge(data) {
  const sentiments = data.sentiment || [];
  const latest = sentiments[sentiments.length - 1];
  if (!latest) return;

  const score = latest.avg_sentiment_score; // -1 to 1
  const pct = ((score + 1) / 2 * 100).toFixed(0); // map to 0-100%
  const fill = document.getElementById('sentiment-fill');
  if (fill) fill.style.width = `${pct}%`;

  const label = document.getElementById('sentiment-label');
  if (label) {
    const cls = colorClass(score);
    const text = score > 0.1 ? 'Bullish' : score < -0.1 ? 'Bearish' : 'Neutral';
    const icon = score > 0.1 ? 'fa-smile' : score < -0.1 ? 'fa-frown' : 'fa-meh';
    label.innerHTML = `<i class="fas ${icon} ${cls}"></i> <span class="${cls}">${text} ${pct}%</span>`;
  }

  const articleCount = document.getElementById('sentiment-article-count');
  if (articleCount) {
    articleCount.innerHTML = `<i class="fas fa-newspaper"></i> ${latest.article_count || 0} articles (24h)`;
  }
}

function renderPriceChart(stockData, predictionsData) {
  const records = stockData.data || [];
  const preds = predictionsData.predictions || [];

  const labels = records.map(r => formatDate(r.date));
  const prices = records.map(r => r.close);

  // Overlay predicted prices starting from last historical point
  const predPrices = new Array(records.length).fill(null);
  if (preds.length > 0 && records.length > 0) {
    predPrices[records.length - 1] = records[records.length - 1].close;
  }

  createLineChart('priceChart', labels, [
    {
      label: `${AppState.currentSymbol} Price`,
      data: prices,
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99,102,241,0.05)',
      borderWidth: 3,
      pointRadius: 3,
      pointBackgroundColor: '#8b5cf6',
      tension: 0.3,
      fill: true,
    },
    {
      label: 'AI Predicted',
      data: predPrices,
      borderColor: '#c084fc',
      borderDash: [6, 6],
      borderWidth: 2,
      pointRadius: 4,
      pointBackgroundColor: '#c084fc',
      tension: 0.2,
    },
  ]);
}

function renderSentimentChart(data) {
  const sentiments = (data.sentiment || []).slice(-7);
  const labels = sentiments.map(s => formatDate(s.date));
  const scores = sentiments.map(s => s.avg_sentiment_score);

  createLineChart('sentimentChart', labels, [
    {
      label: 'Daily Sentiment Score',
      data: scores,
      borderColor: '#34d399',
      backgroundColor: 'rgba(52,211,153,0.1)',
      borderWidth: 3,
      fill: true,
      pointRadius: 5,
      pointBackgroundColor: '#10b981',
    },
  ], {
    scales: {
      y: { min: -1, max: 1, grid: { color: '#1e1f2a' }, ticks: { color: '#9ca3af' } },
      x: { ticks: { color: '#9ca3af' } },
    },
  });
}

function renderHistoryTable(data) {
  const history = (data.history || [])
    .sort((a, b) => new Date(b.prediction_date) - new Date(a.prediction_date))
    .slice(0, 5);

  const container = document.getElementById('history-table');
  if (!container) return;

  if (history.length === 0) {
    container.innerHTML = '<p class="empty-state">No predictions yet</p>';
    return;
  }

  const rows = history.map(h => {
    const delta = h.actual_price != null
      ? ((h.actual_price - h.predicted_price) / h.predicted_price * 100).toFixed(2)
      : null;
    const deltaHtml = delta != null
      ? `<span class="${parseFloat(delta) >= 0 ? 'positive' : 'negative'}">${parseFloat(delta) >= 0 ? '▲' : '▼'} ${Math.abs(delta)}%</span>`
      : '—';
    return `<tr>
      <td>${formatDate(h.prediction_date)}</td>
      <td>${h.symbol || AppState.currentSymbol}</td>
      <td>${formatPrice(h.predicted_price)}</td>
      <td>${h.actual_price != null ? formatPrice(h.actual_price) : 'Pending'}</td>
      <td>${deltaHtml}</td>
    </tr>`;
  }).join('');

  container.innerHTML = `<table>
    <thead><tr>
      <th>Date</th><th>Symbol</th><th>Predicted</th><th>Actual</th><th>Accuracy</th>
    </tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function initAgentChat() {
  const input = document.getElementById('agent-input');
  const sendBtn = document.getElementById('agent-send');
  const messages = document.getElementById('agent-messages');
  if (!input || !sendBtn || !messages) return;

  async function sendQuery() {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';

    // Append user message
    const userMsg = document.createElement('p');
    userMsg.className = 'agent-message user';
    userMsg.textContent = text;
    messages.appendChild(userMsg);
    messages.scrollTop = messages.scrollHeight;

    // Append loading indicator
    const loadingMsg = document.createElement('p');
    loadingMsg.className = 'agent-message';
    loadingMsg.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Thinking...';
    messages.appendChild(loadingMsg);
    messages.scrollTop = messages.scrollHeight;

    try {
      const res = await api.agent.query(text);
      loadingMsg.innerHTML = `<i class="fas fa-robot" style="color:#c084fc;"></i> ${res.response}`;
    } catch (err) {
      loadingMsg.innerHTML = `<i class="fas fa-circle-xmark" style="color:#ef4444;"></i> ${err.message || 'Failed to get response'}`;
    }
    messages.scrollTop = messages.scrollHeight;
  }

  sendBtn.addEventListener('click', sendQuery);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendQuery();
  });
}
