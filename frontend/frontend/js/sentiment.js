import { api } from './api.js';
import { AppState } from './state.js';
import { showToast, formatDate } from './utils.js';
import { createBarChart, destroyChart } from './charts.js';

export function cleanup() {
  destroyChart('sentiment-bar-chart');
}

export async function init() {
  const symbol = AppState.currentSymbol;

  try {
    const data = await api.sentiment.get(symbol);
    const sentiments = data.sentiment || [];
    renderSentimentTable(sentiments);
    renderSentimentBarChart(sentiments);
  } catch (err) {
    showToast(err.message || 'Failed to load sentiment', 'error');
  }

  // Wire analyze button
  const analyzeBtn = document.getElementById('analyze-btn');
  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', async () => {
      analyzeBtn.classList.add('btn-loading');
      try {
        await api.sentiment.analyze(symbol);
        showToast('Sentiment analysis complete', 'success');
        await init(); // refresh
      } catch (err) {
        showToast(err.message || 'Analysis failed', 'error');
      } finally {
        analyzeBtn.classList.remove('btn-loading');
      }
    }, { once: true });
  }
}

function renderSentimentTable(sentiments) {
  const container = document.getElementById('sentiment-table');
  if (!container) return;
  if (sentiments.length === 0) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-chart-simple"></i><p>No sentiment data available</p></div>';
    return;
  }
  const rows = [...sentiments].reverse().map(s => {
    const score = s.avg_sentiment_score;
    const cls = score > 0.1 ? 'positive' : score < -0.1 ? 'negative' : 'neutral';
    const label = score > 0.1 ? 'Bullish' : score < -0.1 ? 'Bearish' : 'Neutral';
    return `<tr>
      <td>${formatDate(s.date)}</td>
      <td><span class="${cls}">${score.toFixed(3)}</span></td>
      <td><span class="${cls}">${label}</span></td>
      <td>${s.article_count}</td>
      <td><span class="positive">+${s.positive_count}</span> / ${s.neutral_count} / <span class="negative">-${s.negative_count}</span></td>
    </tr>`;
  }).join('');
  container.innerHTML = `<table>
    <thead><tr><th>Date</th><th>Score</th><th>Sentiment</th><th>Articles</th><th>+/=/−</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function renderSentimentBarChart(sentiments) {
  const labels = sentiments.map(s => formatDate(s.date));
  const scores = sentiments.map(s => s.avg_sentiment_score);
  const colors = scores.map(s => s > 0.1 ? '#10b981' : s < -0.1 ? '#ef4444' : '#f59e0b');

  createBarChart('sentiment-bar-chart', labels, [{
    label: 'Sentiment Score',
    data: scores,
    backgroundColor: colors,
    borderRadius: 6,
  }], {
    scales: {
      y: { min: -1, max: 1, grid: { color: '#1e1f2a' }, ticks: { color: '#9ca3af' } },
      x: { ticks: { color: '#9ca3af' } },
    },
  });
}
