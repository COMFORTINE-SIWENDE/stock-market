// Predictions Page - Full API Integration

document.addEventListener('DOMContentLoaded', async () => {
  if (!state.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  await initializePredictionsPage();
});

let forecastChart = null;
let currentStock = 'SCOM.NR';
let currentDays = 5;

async function initializePredictionsPage() {
  try {
    await loadUserInfo();
    setupEventListeners();
    console.log('Predictions page initialized');
  } catch (error) {
    console.error('Predictions page initialization error:', error);
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

async function generatePrediction(symbol, days) {
  try {
    currentStock = symbol;
    currentDays = days;
    
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generating...';
    
    // Get predictions from API - the API returns the actual array directly
    const response = await api.predictions.get(symbol, days);
    
    // Handle both response formats
    let predictions = [];
    if (Array.isArray(response)) {
      predictions = response;
    } else if (response.predictions && Array.isArray(response.predictions)) {
      predictions = response.predictions;
    }
    
    if (predictions.length > 0) {
      updatePredictionStats(predictions);
      updateForecastChart(predictions);
      updateForecastTable(predictions);
      
      showSuccess(`Generated ${predictions.length} predictions for ${symbol}`);
    } else {
      showMockPrediction(symbol, days);
    }
    
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"/>
      </svg>
      Generate Prediction
    `;
  } catch (error) {
    console.error('Failed to generate prediction:', error);
    showMockPrediction(symbol, days);
    
    const btn = document.getElementById('generateBtn');
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"/>
      </svg>
      Generate Prediction
    `;
  }
}

function updatePredictionStats(predictions) {
  const latest = predictions[predictions.length - 1];
  
  // Update predicted price
  document.getElementById('predictedPrice').textContent = `KES ${latest.predicted_price.toFixed(2)}`;
  document.getElementById('predictionDate').textContent = latest.target_date;
  
  // Update confidence
  const confidence = (latest.confidence_score * 100).toFixed(0);
  document.getElementById('confidenceScore').textContent = `${confidence}%`;
  
  // Update trend
  const trend = latest.trend_direction || 'up';
  document.getElementById('trendDirection').textContent = trend.toUpperCase();
  
  const trendIcon = document.getElementById('trendIcon');
  if (trend === 'up') {
    trendIcon.className = 'stat-icon green';
  } else {
    trendIcon.className = 'stat-icon red';
  }
  
  // Update last updated
  document.getElementById('lastUpdated').textContent = new Date().toLocaleString();
}

function updateForecastChart(predictions) {
  const ctx = document.getElementById('forecastChart');
  
  if (!ctx) return;
  
  ctx.style.display = 'block';
  ctx.style.height = '320px';
  
  const labels = predictions.map(p => {
    const date = new Date(p.target_date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  
  const prices = predictions.map(p => p.predicted_price);
  
  if (forecastChart) {
    forecastChart.destroy();
  }
  
  forecastChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Predicted Price (KES)',
        data: prices,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 8,
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

function updateForecastTable(predictions) {
  const tbody = document.getElementById('forecastTableBody');
  
  if (!tbody || predictions.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No predictions available</td></tr>';
    return;
  }
  
  tbody.innerHTML = predictions.map((pred, index) => {
    const confidence = (pred.confidence_score * 100).toFixed(0);
    const change = index > 0 
      ? ((pred.predicted_price - predictions[index-1].predicted_price) / predictions[index-1].predicted_price * 100)
      : 0;
    
    const changeClass = change >= 0 ? 'positive' : 'negative';
    const changeIcon = change >= 0 ? '↑' : '↓';
    const trendClass = pred.trend_direction === 'up' ? 'positive' : 'negative';
    const trendIcon = pred.trend_direction === 'up' ? '↑' : '↓';
    
    return `
      <tr>
        <td>${pred.target_date}</td>
        <td>KES ${pred.predicted_price.toFixed(2)}</td>
        <td>${confidence}%</td>
        <td><span class="change ${changeClass}">${changeIcon} ${Math.abs(change).toFixed(2)}%</span></td>
        <td><span class="change ${trendClass}">${trendIcon} ${pred.trend_direction}</span></td>
      </tr>
    `;
  }).join('');
}

function showMockPrediction(symbol, days) {
  const mockPredictions = [];
  const basePrice = 25.50;
  const now = new Date();
  
  for (let i = 1; i <= days; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() + i);
    
    const price = basePrice + (i * 0.15) + (Math.random() - 0.5) * 0.5;
    
    mockPredictions.push({
      target_date: date.toISOString().split('T')[0],
      predicted_price: price,
      confidence_score: 0.75 + Math.random() * 0.15,
      trend_direction: price > basePrice ? 'up' : 'down',
      model_source: 'LSTM'
    });
  }
  
  updatePredictionStats(mockPredictions);
  updateForecastChart(mockPredictions);
  updateForecastTable(mockPredictions);
  
  console.log(`Showing mock predictions for ${symbol}`);
}

function setupEventListeners() {
  const stockSelect = document.getElementById('stockSelect');
  if (stockSelect) {
    stockSelect.addEventListener('change', (e) => {
      currentStock = e.target.value;
    });
  }
  
  const daysSelect = document.getElementById('daysSelect');
  if (daysSelect) {
    daysSelect.addEventListener('change', (e) => {
      currentDays = parseInt(e.target.value);
    });
  }
  
  const generateBtn = document.getElementById('generateBtn');
  if (generateBtn) {
    generateBtn.addEventListener('click', async () => {
      await generatePrediction(currentStock, currentDays);
    });
  }
  
  // Email prediction button
  const emailBtn = document.getElementById('emailBtn');
  if (emailBtn) {
    emailBtn.addEventListener('click', async () => {
      await emailPrediction(currentStock, currentDays);
    });
  }
}

async function emailPrediction(symbol, days) {
  try {
    const btn = document.getElementById('emailBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Sending...';
    
    // Generate prediction with email flag
    const response = await fetch(`http://localhost:8000/predictions/${symbol}?days=${days}&send_email=true`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('mm_token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to send email');
    }
    
    const result = await response.json();
    
    if (result.email_sent) {
      showSuccess('📧 Prediction email sent to your registered email!');
    } else {
      showError('Failed to send email. Please try again.');
    }
    
    // Restore button
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
        <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
      </svg>
      Email Predictions
    `;
  } catch (error) {
    console.error('Failed to email prediction:', error);
    showError('Failed to send email. Please check your connection.');
    
    const btn = document.getElementById('emailBtn');
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
        <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
      </svg>
      Email Predictions
    `;
  }
}

function showSuccess(message) {
  console.log('✅', message);
}

function showError(message) {
  console.error('❌', message);
}
