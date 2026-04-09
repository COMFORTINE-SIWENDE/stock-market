import { api } from './api.js';
import { AppState } from './state.js';
import { showToast, formatDate, formatPrice, daysAgo, today } from './utils.js';
import { createLineChart, destroyChart } from './charts.js';

const PAGE_SIZE = 20;
let _allData = [];
let _currentPage = 1;

export function cleanup() {
  destroyChart('stocks-chart');
  _allData = [];
  _currentPage = 1;
}

export async function init() {
  const symbol = AppState.currentSymbol;

  const [dataRes, indicatorsRes] = await Promise.allSettled([
    api.stocks.data(symbol, daysAgo(30), today()),
    api.stocks.indicators(symbol),
  ]);

  // Render indicators card
  if (indicatorsRes.status === 'fulfilled') {
    const ind = indicatorsRes.value.indicators || {};
    const sma5 = document.getElementById('ind-sma5');
    const sma20 = document.getElementById('ind-sma20');
    const vol = document.getElementById('ind-volatility');
    if (sma5) sma5.textContent = ind.sma_5 != null ? formatPrice(ind.sma_5) : '—';
    if (sma20) sma20.textContent = ind.sma_20 != null ? formatPrice(ind.sma_20) : '—';
    if (vol) vol.textContent = ind.volatility != null ? (ind.volatility * 100).toFixed(2) + '%' : '—';
  } else {
    showToast(indicatorsRes.reason?.message || 'Failed to load indicators', 'error');
  }

  // Render table and chart
  if (dataRes.status === 'fulfilled') {
    _allData = dataRes.value.data || [];
    if (_allData.length === 0) {
      const tableEl = document.getElementById('stocks-table');
      if (tableEl) tableEl.innerHTML = '<div class="empty-state"><i class="fas fa-database"></i><p>No data available — click Collect Data to fetch records</p></div>';
    } else {
      renderStocksTable(_allData, 1);
      renderStocksChart(_allData, indicatorsRes.status === 'fulfilled' ? indicatorsRes.value.indicators : null);
    }
  } else {
    showToast(dataRes.reason?.message || 'Failed to load stock data', 'error');
  }

  // Wire collect button
  const collectBtn = document.getElementById('collect-btn');
  if (collectBtn) {
    collectBtn.addEventListener('click', async () => {
      collectBtn.classList.add('btn-loading');
      try {
        const res = await api.stocks.collect([symbol], 365);
        const info = res[symbol] || {};
        showToast(`${info.stock_records ?? 0} stock records, ${info.news_articles ?? 0} news articles inserted`, 'success');
        await init();
      } catch (err) {
        showToast(err.message || 'Data collection failed', 'error');
      } finally {
        collectBtn.classList.remove('btn-loading');
      }
    }, { once: true });
  }
}

function renderStocksTable(data, page) {
  _currentPage = page;
  const container = document.getElementById('stocks-table');
  const pagination = document.getElementById('pagination');
  if (!container) return;

  const start = (page - 1) * PAGE_SIZE;
  const pageData = [...data].reverse().slice(start, start + PAGE_SIZE);

  const rows = pageData.map(r => `<tr>
    <td>${formatDate(r.date)}</td>
    <td>${formatPrice(r.open)}</td>
    <td>${formatPrice(r.high)}</td>
    <td>${formatPrice(r.low)}</td>
    <td>${formatPrice(r.close)}</td>
    <td>${(r.volume / 1_000_000).toFixed(1)}M</td>
    <td>${formatPrice(r.adj_close)}</td>
  </tr>`).join('');

  container.innerHTML = `<table>
    <thead><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th><th>Adj Close</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;

  // Pagination
  if (pagination) {
    const totalPages = Math.ceil(data.length / PAGE_SIZE);
    let btns = '';
    for (let i = 1; i <= totalPages; i++) {
      btns += `<button class="btn-outline${i === page ? ' active' : ''}" style="padding:6px 14px;font-size:0.8rem;" data-page="${i}">${i}</button>`;
    }
    pagination.innerHTML = btns;
    pagination.querySelectorAll('[data-page]').forEach(btn => {
      btn.addEventListener('click', () => renderStocksTable(data, parseInt(btn.dataset.page)));
    });
  }
}

function renderStocksChart(data, indicators) {
  const labels = data.map(r => formatDate(r.date));
  const closes = data.map(r => r.close);

  const datasets = [
    {
      label: 'Close Price',
      data: closes,
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99,102,241,0.05)',
      borderWidth: 2,
      pointRadius: 2,
      tension: 0.3,
      fill: true,
    },
  ];

  if (indicators?.sma_5) {
    datasets.push({
      label: 'SMA 5',
      data: new Array(closes.length).fill(indicators.sma_5),
      borderColor: '#f59e0b',
      borderWidth: 1.5,
      borderDash: [4, 4],
      pointRadius: 0,
    });
  }
  if (indicators?.sma_20) {
    datasets.push({
      label: 'SMA 20',
      data: new Array(closes.length).fill(indicators.sma_20),
      borderColor: '#34d399',
      borderWidth: 1.5,
      borderDash: [4, 4],
      pointRadius: 0,
    });
  }

  createLineChart('stocks-chart', labels, datasets);
}
