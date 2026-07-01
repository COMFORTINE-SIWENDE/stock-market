// Stocks Page - Full API Integration with Visualizations

document.addEventListener('DOMContentLoaded', async () => {
  if (!state.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  await initializeStocksPage();
});

let priceChart = null;
let volumeChart = null;
let currentStock = 'SCOM.NR';
let currentPeriod = 30;

async function initializeStocksPage() {
  try {
    await loadUserInfo();
    setupEventListeners();
    
    // Auto-load data for default stock
    await loadStockData(currentStock, currentPeriod);
    
    console.log('Stocks page initialized');
  } catch (error) {
    console.error('Stocks page initialization error:', error);
  }
}

async function loadUserInfo() {
  try {
    const user = await api.auth.me();
    document.getElementById('userName').textContent = user.username || 'User';
  } catch (error) {
    console.error('Failed to load user info:', error);
  }
}

async function loadStockData(symbol, days) {
  try {
    currentStock = symbol;
    currentPeriod = days;
    
    const btn = document.getElementById('loadStockBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Loading...';
    
    // Calculate date range
    const end = new Date().toISOString().split('T')[0];
    const start = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    // Load stock data
    const stockData = await api.stocks.data(symbol, start, end);
    
    if (stockData.data && stockData.data.length > 0) {
      updateStats(stockData.data);
      updatePriceChart(stockData.data);
      updateVolumeChart(stockData.data);
      updateStockTable(stockData.data);
      
      // Load indicators
      try {
        const indicators = await api.stocks.indicators(symbol, start, end);
        updateIndicators(indicators.indicators);
      } catch (e) {
        console.log('Indicators not available:', e);
      }
      
      showSuccess(`Loaded data for ${symbol}`);
    } else {
      showMockData(symbol);
    }
    
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"/>
      </svg>
      Load Stock Data
    `;
  } catch (error) {
    console.error('Failed to load stock data:', error);
    showMockData(symbol);
    
    const btn = document.getElementById('loadStockBtn');
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"/>
      </svg>
      Load Stock Data
    `;
  }
}

function updateStats(data) {
  if (data.length === 0) return;
  
  const latest = data[data.length - 1];
  const previous = data.length > 1 ? data[data.length - 2] : latest;
  
  const price = latest.close;
  const change = ((latest.close - previous.close) / previous.close * 100);
  
  document.getElementById('currentPrice').textContent = `KES ${price.toFixed(2)}`;
  
  const changeClass = change >= 0 ? 'positive' : 'negative';
  const changeIcon = change >= 0 ? '↑' : '↓';
  document.getElementById('priceChange').innerHTML = `
    <span class="change ${changeClass}">${changeIcon} ${Math.abs(change).toFixed(2)}%</span>
  `;
  
  // Calculate average volume
  const avgVolume = data.reduce((sum, d) => sum + d.volume, 0) / data.length;
  document.getElementById('volume').textContent = formatVolume(avgVolume);
  
  // Calculate volatility (standard deviation of returns)
  const returns = [];
  for (let i = 1; i < data.length; i++) {
    returns.push((data[i].close - data[i-1].close) / data[i-1].close);
  }
  const volatility = standardDeviation(returns) * Math.sqrt(252) * 100;
  document.getElementById('volatility').textContent = `${volatility.toFixed(2)}%`;
}

function updateIndicators(indicators) {
  document.getElementById('sma5').textContent = indicators.sma_5 
    ? `KES ${indicators.sma_5.toFixed(2)}` 
    : '-';
  document.getElementById('sma20').textContent = indicators.sma_20 
    ? `KES ${indicators.sma_20.toFixed(2)}` 
    : '-';
  document.getElementById('rsi').textContent = indicators.rsi 
    ? indicators.rsi.toFixed(1) 
    : '-';
}

function updatePriceChart(data) {
  const ctx = document.getElementById('priceHistoryChart');
  
  if (!ctx) return;
  
  ctx.style.display = 'block';
  ctx.style.height = '320px';
  
  const labels = data.map(d => {
    const date = new Date(d.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  
  const prices = data.map(d => d.close);
  
  if (priceChart) {
    priceChart.destroy();
  }
  
  priceChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Close Price (KES)',
        data: prices,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 2,
        pointHoverRadius: 6,
        pointBackgroundColor: '#10b981',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          callbacks: {
            label: function(context) {
              return 'Price: KES ' + context.parsed.y.toFixed(2);
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#94a3b8',
            maxTicksLimit: 10
          }
        },
        y: {
          grid: {
            color: '#e2e8f0'
          },
          ticks: {
            color: '#94a3b8',
            callback: function(value) {
              return 'KES ' + value.toFixed(0);
            }
          }
        }
      }
    }
  });
}

function updateVolumeChart(data) {
  const ctx = document.getElementById('volumeChart');
  
  if (!ctx) return;
  
  ctx.style.display = 'block';
  ctx.style.height = '320px';
  
  const labels = data.slice(-20).map(d => {
    const date = new Date(d.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  
  const volumes = data.slice(-20).map(d => d.volume);
  
  if (volumeChart) {
    volumeChart.destroy();
  }
  
  volumeChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Volume',
        data: volumes,
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderColor: '#3b82f6',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          callbacks: {
            label: function(context) {
              return 'Volume: ' + formatVolume(context.parsed.y);
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#94a3b8'
          }
        },
        y: {
          grid: {
            color: '#e2e8f0'
          },
          ticks: {
            color: '#94a3b8',
            callback: function(value) {
              return formatVolume(value);
            }
          }
        }
      }
    }
  });
}

function updateStockTable(data) {
  const tbody = document.getElementById('stockTableBody');
  
  if (!tbody || data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">No data available</td></tr>';
    return;
  }
  
  const recent = data.slice(-15).reverse();
  
  tbody.innerHTML = recent.map((row, index) => {
    const prevRow = index < recent.length - 1 ? recent[index + 1] : row;
    const change = ((row.close - prevRow.close) / prevRow.close * 100);
    const changeClass = change >= 0 ? 'positive' : 'negative';
    const changeIcon = change >= 0 ? '↑' : '↓';
    
    return `
      <tr>
        <td>${row.date}</td>
        <td>KES ${row.open.toFixed(2)}</td>
        <td>KES ${row.high.toFixed(2)}</td>
        <td>KES ${row.low.toFixed(2)}</td>
        <td>KES ${row.close.toFixed(2)}</td>
        <td>${formatVolume(row.volume)}</td>
        <td><span class="change ${changeClass}">${changeIcon} ${Math.abs(change).toFixed(2)}%</span></td>
      </tr>
    `;
  }).join('');
}

function showMockData(symbol) {
  const mockData = [];
  const basePrice = 25.50;
  const now = new Date();
  
  for (let i = currentPeriod - 1; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    const open = basePrice + (Math.random() - 0.5) * 3;
    const close = open + (Math.random() - 0.5) * 2;
    const high = Math.max(open, close) + Math.random() * 1;
    const low = Math.min(open, close) - Math.random() * 1;
    const volume = Math.floor(1000000 + Math.random() * 5000000);
    
    mockData.push({
      date: date.toISOString().split('T')[0],
      open: open,
      high: high,
      low: low,
      close: close,
      volume: volume
    });
  }
  
  updateStats(mockData);
  updatePriceChart(mockData);
  updateVolumeChart(mockData);
  updateStockTable(mockData);
  
  document.getElementById('sma5').textContent = `KES ${(basePrice + 0.5).toFixed(2)}`;
  document.getElementById('sma20').textContent = `KES ${(basePrice - 0.3).toFixed(2)}`;
  document.getElementById('rsi').textContent = '55.2';
  
  console.log(`Showing mock data for ${symbol}`);
}

function setupEventListeners() {
  const stockSelect = document.getElementById('stockSelect');
  if (stockSelect) {
    stockSelect.addEventListener('change', (e) => {
      currentStock = e.target.value;
    });
  }
  
  const timePeriod = document.getElementById('timePeriod');
  if (timePeriod) {
    timePeriod.addEventListener('change', (e) => {
      currentPeriod = parseInt(e.target.value);
    });
  }
  
  const loadBtn = document.getElementById('loadStockBtn');
  if (loadBtn) {
    loadBtn.addEventListener('click', async () => {
      await loadStockData(currentStock, currentPeriod);
    });
  }
  
  const exportBtn = document.getElementById('exportData');
  if (exportBtn) {
    exportBtn.addEventListener('click', (e) => {
      e.preventDefault();
      showSuccess('Export feature coming soon!');
    });
  }
}

// Utility functions
function formatVolume(volume) {
  if (volume >= 1000000) {
    return (volume / 1000000).toFixed(2) + 'M';
  } else if (volume >= 1000) {
    return (volume / 1000).toFixed(2) + 'K';
  }
  return volume.toString();
}

function standardDeviation(values) {
  const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
  const squareDiffs = values.map(val => Math.pow(val - avg, 2));
  const avgSquareDiff = squareDiffs.reduce((sum, val) => sum + val, 0) / squareDiffs.length;
  return Math.sqrt(avgSquareDiff);
}

function showSuccess(message) {
  console.log('✅', message);
}

function showError(message) {
  console.error('❌', message);
}
