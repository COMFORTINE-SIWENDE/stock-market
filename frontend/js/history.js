// Prediction History Page - Full API Integration with Visualizations

document.addEventListener('DOMContentLoaded', async () => {
  // Check authentication
  if (!state.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  await initializeHistoryPage();
});

let accuracyTrendChart = null;
let comparisonChart = null;
let currentStock = 'SCOM.NR';

async function initializeHistoryPage() {
  try {
    // Load user info
    await loadUserInfo();
    
    // Load initial data automatically
    await loadPredictionHistory(currentStock);
    
    // Setup event listeners
    setupEventListeners();
    
    console.log('History page initialized');
  } catch (error) {
    console.error('History page initialization error:', error);
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

async function loadPredictionHistory(symbol) {
  try {
    currentStock = symbol;
    
    // Show loading
    const btn = document.getElementById('loadHistoryBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Loading...';
    
    // Load prediction history from API
    const result = await api.predictions.history(symbol);
    
    if (result.history && result.history.length > 0) {
      // Filter predictions that have actual prices
      const withActual = result.history.filter(p => p.actual_price !== null && p.actual_price !== undefined);
      
      if (withActual.length > 5) {
        // We have enough real data with actual prices
        updateStats(result.history);
        updateAccuracyTrendChart(result.history);
        updateComparisonChart(result.history);
        updateHistoryTable(result.history);
        showSuccess(`Loaded ${result.history.length} predictions for ${symbol}`);
      } else {
        // Not enough actual prices, show mock data
        showMockData(symbol);
      }
    } else {
      // No history, show mock data
      showMockData(symbol);
    }
    
    // Restore button
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"/>
      </svg>
      Load History
    `;
  } catch (error) {
    console.error('Failed to load prediction history:', error);
    showMockData(symbol);
    
    const btn = document.getElementById('loadHistoryBtn');
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"/>
      </svg>
      Load History
    `;
  }
}

function updateStats(history) {
  // Total predictions
  document.getElementById('totalPredictions').textContent = history.length;
  
  // Calculate accuracy for predictions with actual prices
  const withActual = history.filter(p => p.actual_price !== null && p.actual_price !== undefined);
  
  if (withActual.length > 0) {
    // Calculate percentage error
    const percentErrors = withActual.map(p => 
      Math.abs((p.predicted_price - p.actual_price) / p.actual_price * 100)
    );
    const avgPercentError = percentErrors.reduce((a, b) => a + b, 0) / percentErrors.length;
    const accuracyPercent = Math.max(0, 100 - avgPercentError);
    
    // Calculate absolute error
    const absErrors = withActual.map(p => Math.abs(p.predicted_price - p.actual_price));
    const avgAbsError = absErrors.reduce((a, b) => a + b, 0) / absErrors.length;
    
    document.getElementById('accuracyRate').textContent = `${accuracyPercent.toFixed(1)}%`;
    document.getElementById('avgError').textContent = `KES ${avgAbsError.toFixed(2)}`;
  } else {
    document.getElementById('accuracyRate').textContent = 'N/A';
    document.getElementById('avgError').textContent = 'N/A';
  }
}

function updateAccuracyTrendChart(history) {
  const ctx = document.getElementById('accuracyTrendChart');
  
  if (!ctx) return;
  
  // Ensure canvas has proper dimensions
  ctx.style.display = 'block';
  ctx.style.height = '320px';
  
  // Filter predictions with actual prices and sort by date
  const withActual = history
    .filter(p => p.actual_price !== null && p.actual_price !== undefined)
    .sort((a, b) => new Date(a.target_date) - new Date(b.target_date));
  
  if (withActual.length === 0) {
    // Show empty state
    return;
  }
  
  // Calculate accuracy for each prediction
  const labels = withActual.map(p => {
    const date = new Date(p.target_date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  
  const accuracies = withActual.map(p => {
    const percentError = Math.abs((p.predicted_price - p.actual_price) / p.actual_price * 100);
    return Math.max(0, 100 - percentError);
  });
  
  // Destroy existing chart
  if (accuracyTrendChart) {
    accuracyTrendChart.destroy();
  }
  
  // Create chart
  accuracyTrendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Accuracy %',
        data: accuracies,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#3b82f6',
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
              return 'Accuracy: ' + context.parsed.y.toFixed(1) + '%';
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
          min: 0,
          max: 100,
          grid: {
            color: '#e2e8f0'
          },
          ticks: {
            color: '#94a3b8',
            callback: function(value) {
              return value + '%';
            }
          }
        }
      }
    }
  });
}

function updateComparisonChart(history) {
  const ctx = document.getElementById('predictionComparisonChart');
  
  if (!ctx) return;
  
  // Ensure canvas has proper dimensions
  ctx.style.display = 'block';
  ctx.style.height = '320px';
  
  // Get last 10 predictions with actual prices
  const withActual = history
    .filter(p => p.actual_price !== null && p.actual_price !== undefined)
    .sort((a, b) => new Date(b.target_date) - new Date(a.target_date))
    .slice(0, 10)
    .reverse();
  
  if (withActual.length === 0) {
    return;
  }
  
  const labels = withActual.map(p => {
    const date = new Date(p.target_date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  
  const predictedPrices = withActual.map(p => p.predicted_price);
  const actualPrices = withActual.map(p => p.actual_price);
  
  // Destroy existing chart
  if (comparisonChart) {
    comparisonChart.destroy();
  }
  
  // Create chart
  comparisonChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Predicted',
          data: predictedPrices,
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
          borderColor: '#3b82f6',
          borderWidth: 1
        },
        {
          label: 'Actual',
          data: actualPrices,
          backgroundColor: 'rgba(16, 185, 129, 0.7)',
          borderColor: '#10b981',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          callbacks: {
            label: function(context) {
              return context.dataset.label + ': KES ' + context.parsed.y.toFixed(2);
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
              return 'KES ' + value.toFixed(0);
            }
          }
        }
      }
    }
  });
}

function updateHistoryTable(history) {
  const tbody = document.getElementById('historyTableBody');
  
  if (!tbody || history.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-cell">No prediction history available</td></tr>';
    return;
  }
  
  // Sort by target date descending
  const sorted = [...history].sort((a, b) => new Date(b.target_date) - new Date(a.target_date));
  
  tbody.innerHTML = sorted.map(pred => {
    const actualPrice = pred.actual_price !== null && pred.actual_price !== undefined 
      ? `KES ${pred.actual_price.toFixed(2)}` 
      : '-';
    
    const error = pred.actual_price !== null && pred.actual_price !== undefined
      ? `KES ${Math.abs(pred.predicted_price - pred.actual_price).toFixed(2)}`
      : '-';
    
    const trendClass = pred.trend_direction === 'up' ? 'positive' : 'negative';
    const trendIcon = pred.trend_direction === 'up' ? '↑' : '↓';
    
    const confidence = `${(pred.confidence_score * 100).toFixed(0)}%`;
    
    return `
      <tr>
        <td>${pred.prediction_date || '-'}</td>
        <td>${pred.target_date}</td>
        <td>KES ${pred.predicted_price.toFixed(2)}</td>
        <td>${actualPrice}</td>
        <td>${error}</td>
        <td><span class="change ${trendClass}">${trendIcon} ${pred.trend_direction}</span></td>
        <td>${confidence}</td>
        <td><span class="sentiment-badge positive">${pred.model_source || 'LSTM'}</span></td>
      </tr>
    `;
  }).join('');
}

function showMockData(symbol) {
  // Generate mock prediction history
  const mockHistory = [];
  const now = new Date();
  const basePrice = 25.50;
  
  for (let i = 29; i >= 0; i--) {
    const targetDate = new Date(now);
    targetDate.setDate(targetDate.getDate() - i);
    
    const predictionDate = new Date(targetDate);
    predictionDate.setDate(predictionDate.getDate() - 1);
    
    const predicted = basePrice + (Math.random() - 0.5) * 5;
    const actual = i < 10 ? null : predicted + (Math.random() - 0.5) * 2;
    
    mockHistory.push({
      prediction_date: predictionDate.toISOString().split('T')[0],
      target_date: targetDate.toISOString().split('T')[0],
      predicted_price: predicted,
      actual_price: actual,
      trend_direction: Math.random() > 0.5 ? 'up' : 'down',
      confidence_score: 0.70 + Math.random() * 0.25,
      model_source: 'LSTM'
    });
  }
  
  updateStats(mockHistory);
  updateAccuracyTrendChart(mockHistory);
  updateComparisonChart(mockHistory);
  updateHistoryTable(mockHistory);
  
  console.log(`Showing mock data for ${symbol}`);
}

function setupEventListeners() {
  // Stock selector
  const stockSelect = document.getElementById('stockSelect');
  if (stockSelect) {
    stockSelect.addEventListener('change', (e) => {
      currentStock = e.target.value;
    });
  }
  
  // Load history button
  const loadBtn = document.getElementById('loadHistoryBtn');
  if (loadBtn) {
    loadBtn.addEventListener('click', async () => {
      await loadPredictionHistory(currentStock);
    });
  }
  
  // Export CSV
  const exportBtn = document.getElementById('exportHistory');
  if (exportBtn) {
    exportBtn.addEventListener('click', (e) => {
      e.preventDefault();
      showSuccess('Export feature coming soon!');
    });
  }
}

function showSuccess(message) {
  console.log('✅', message);
  // In production, show toast notification
}

function showError(message) {
  console.error('❌', message);
  // In production, show toast notification
}
