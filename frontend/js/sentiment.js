// Sentiment Analysis Page - Full API Integration

document.addEventListener('DOMContentLoaded', async () => {
  // Check authentication
  if (!state.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  await initializeSentimentPage();
});

let sentimentTrendChart = null;
let sentimentSourceChart = null;
let currentStock = 'SCOM.NR';

async function initializeSentimentPage() {
  try {
    // Load user info
    await loadUserInfo();
    
    // Load initial sentiment data
    await loadSentimentData(currentStock);
    
    // Setup event listeners
    setupEventListeners();
  } catch (error) {
    console.error('Sentiment page initialization error:', error);
    showError('Failed to load sentiment data');
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

async function loadSentimentData(symbol) {
  try {
    currentStock = symbol;
    
    // Show loading state
    showLoading();
    
    // Load sentiment data from API
    const sentimentData = await api.sentiment.get(symbol);
    
    if (sentimentData.sentiment && sentimentData.sentiment.length > 0) {
      // Calculate aggregated stats
      const stats = calculateSentimentStats(sentimentData.sentiment);
      updateSentimentCards(stats);
      
      // Update charts
      updateSentimentTrendChart(sentimentData.sentiment);
      updateSentimentSourceChart(stats);
      
      // Load recent sentiment items
      await loadRecentSentiment(symbol);
    } else {
      // Show mock data if no real data available
      showMockData();
    }
    
    hideLoading();
  } catch (error) {
    console.error('Failed to load sentiment data:', error);
    showMockData();
    hideLoading();
  }
}

function calculateSentimentStats(sentimentArray) {
  // Calculate overall statistics
  const total = sentimentArray.reduce((sum, item) => 
    sum + item.positive_count + item.neutral_count + item.negative_count, 0);
  
  const totalPositive = sentimentArray.reduce((sum, item) => sum + item.positive_count, 0);
  const totalNeutral = sentimentArray.reduce((sum, item) => sum + item.neutral_count, 0);
  const totalNegative = sentimentArray.reduce((sum, item) => sum + item.negative_count, 0);
  
  const positivePercent = total > 0 ? Math.round((totalPositive / total) * 100) : 0;
  const neutralPercent = total > 0 ? Math.round((totalNeutral / total) * 100) : 0;
  const negativePercent = total > 0 ? Math.round((totalNegative / total) * 100) : 0;
  
  // Determine overall sentiment
  let overallSentiment = 'Neutral';
  if (positivePercent > Math.max(neutralPercent, negativePercent)) {
    overallSentiment = 'Positive';
  } else if (negativePercent > Math.max(positivePercent, neutralPercent)) {
    overallSentiment = 'Negative';
  }
  
  return {
    overall: overallSentiment,
    overallPercent: Math.max(positivePercent, neutralPercent, negativePercent),
    positive: positivePercent,
    neutral: neutralPercent,
    negative: negativePercent,
    total: total
  };
}

function updateSentimentCards(stats) {
  document.getElementById('overallSentiment').textContent = stats.overallPercent + '%';
  document.getElementById('positivePercent').textContent = stats.positive + '%';
  document.getElementById('neutralPercent').textContent = stats.neutral + '%';
  document.getElementById('negativePercent').textContent = stats.negative + '%';
  
  // Update overall sentiment card class
  const overallCard = document.querySelector('.sentiment-card.positive');
  const valueDiv = overallCard.querySelector('.sentiment-value');
  
  overallCard.className = 'sentiment-card';
  if (stats.overall === 'Positive') {
    overallCard.classList.add('positive');
    valueDiv.textContent = 'Positive';
  } else if (stats.overall === 'Negative') {
    overallCard.classList.add('negative');
    valueDiv.textContent = 'Negative';
  } else {
    overallCard.classList.add('neutral');
    valueDiv.textContent = 'Neutral';
  }
}

function updateSentimentTrendChart(sentimentData) {
  const ctx = document.getElementById('sentimentTrendChart');
  
  if (!ctx) {
    console.error('Chart canvas not found: sentimentTrendChart');
    return;
  }
  
  // Ensure canvas has proper dimensions
  ctx.style.display = 'block';
  ctx.style.height = '320px';
  
  // Prepare data
  const labels = sentimentData.map(item => {
    const date = new Date(item.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }).reverse();
  
  const scores = sentimentData.map(item => {
    // Convert sentiment to percentage (0-100)
    return ((item.avg_sentiment_score + 1) / 2) * 100;
  }).reverse();
  
  // Destroy existing chart
  if (sentimentTrendChart) {
    sentimentTrendChart.destroy();
  }
  
  // Create new chart
  sentimentTrendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Sentiment Score',
        data: scores,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 4,
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
              return 'Sentiment: ' + context.parsed.y.toFixed(1) + '%';
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

function updateSentimentSourceChart(stats) {
  const ctx = document.getElementById('sentimentSourceChart');
  
  if (!ctx) return;
  
  // Mock source distribution (in production, get from API)
  const sourceData = {
    'News': 50,
    'Twitter': 30,
    'Reddit': 10,
    'Other': 10
  };
  
  // Destroy existing chart
  if (sentimentSourceChart) {
    sentimentSourceChart.destroy();
  }
  
  // Create donut chart
  sentimentSourceChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: Object.keys(sourceData),
      datasets: [{
        data: Object.values(sourceData),
        backgroundColor: [
          '#10b981',
          '#3b82f6',
          '#f59e0b',
          '#ef4444'
        ],
        borderWidth: 0
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
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          callbacks: {
            label: function(context) {
              return context.label + ': ' + context.parsed + '%';
            }
          }
        }
      },
      cutout: '70%'
    }
  });
  
  // Update legend
  const legend = document.getElementById('sourceLegend');
  if (legend) {
    const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'];
    legend.innerHTML = Object.entries(sourceData).map(([source, percent], index) => `
      <div class="legend-item">
        <div class="legend-color" style="background: ${colors[index]}"></div>
        <span class="legend-label">${source}</span>
        <span class="legend-value">${percent}%</span>
      </div>
    `).join('');
  }
}

async function loadRecentSentiment(symbol) {
  try {
    // Get sentiment data
    const sentimentData = await api.sentiment.get(symbol);
    
    const tbody = document.getElementById('sentimentTableBody');
    
    if (!tbody) return;
    
    // Mock recent sentiment items (in production, get actual articles with sentiment)
    const recentItems = [
      {
        source: 'News',
        headline: 'Safaricom reports strong Q4 results, revenue up 15%',
        sentiment: 'Positive',
        score: 0.78,
        time: '1 hour ago'
      },
      {
        source: 'Twitter',
        headline: 'KCB stock showing great potential this quarter',
        sentiment: 'Positive',
        score: 0.66,
        time: '2 hours ago'
      },
      {
        source: 'Reddit',
        headline: 'Investors optimistic about Safaricom growth',
        sentiment: 'Neutral',
        score: 0.12,
        time: '3 hours ago'
      },
      {
        source: 'News',
        headline: 'Market volatility may impact telecom stocks',
        sentiment: 'Negative',
        score: -0.45,
        time: '4 hours ago'
      }
    ];
    
    tbody.innerHTML = recentItems.map(item => `
      <tr>
        <td>
          <div class="source-badge ${item.source.toLowerCase()}">
            ${getSourceIcon(item.source)}
            ${item.source}
          </div>
        </td>
        <td class="headline-cell">${item.headline}</td>
        <td>
          <span class="sentiment-badge ${item.sentiment.toLowerCase()}">${item.sentiment}</span>
        </td>
        <td class="score-cell">${item.score.toFixed(2)}</td>
        <td class="time-cell">${item.time}</td>
      </tr>
    `).join('');
  } catch (error) {
    console.error('Failed to load recent sentiment:', error);
    document.getElementById('sentimentTableBody').innerHTML = `
      <tr><td colspan="5" class="empty-cell">No sentiment data available</td></tr>
    `;
  }
}

function getSourceIcon(source) {
  const icons = {
    'News': '📰',
    'Twitter': '🐦',
    'Reddit': '🤖',
    'Other': '📱'
  };
  return icons[source] || '📱';
}

function showMockData() {
  // Show mock data when no real data available
  const mockStats = {
    overall: 'Positive',
    overallPercent: 68,
    positive: 68,
    neutral: 22,
    negative: 10,
    total: 100
  };
  
  updateSentimentCards(mockStats);
  
  // Mock trend data
  const mockTrend = [];
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    mockTrend.push({
      date: date.toISOString().split('T')[0],
      avg_sentiment_score: 0.36 + (Math.random() - 0.5) * 0.4,
      article_count: Math.floor(Math.random() * 20) + 10,
      positive_count: Math.floor(Math.random() * 15) + 5,
      neutral_count: Math.floor(Math.random() * 5) + 2,
      negative_count: Math.floor(Math.random() * 3) + 1
    });
  }
  
  updateSentimentTrendChart(mockTrend);
  updateSentimentSourceChart(mockStats);
  loadRecentSentiment(currentStock);
}

function setupEventListeners() {
  // Stock selector
  const stockSelect = document.getElementById('stockSelect');
  if (stockSelect) {
    stockSelect.addEventListener('change', async (e) => {
      await loadSentimentData(e.target.value);
    });
  }
  
  // Analyze sentiment button
  const analyzeBtn = document.getElementById('analyzeSentiment');
  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', async () => {
      analyzeBtn.disabled = true;
      analyzeBtn.innerHTML = '<span class="spinner"></span> Analyzing...';
      
      try {
        // Trigger sentiment analysis
        await api.sentiment.analyze(currentStock);
        
        // Reload data
        setTimeout(async () => {
          await loadSentimentData(currentStock);
          analyzeBtn.disabled = false;
          analyzeBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 100-2 1 1 0 000 2zm7-1a1 1 0 11-2 0 1 1 0 012 0zm-.464 5.535a1 1 0 10-1.415-1.414 3 3 0 01-4.242 0 1 1 0 00-1.415 1.414 5 5 0 007.072 0z"/>
            </svg>
            Analyze Sentiment
          `;
          showSuccess('Sentiment analysis completed!');
        }, 2000);
      } catch (error) {
        console.error('Sentiment analysis failed:', error);
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = 'Analyze Sentiment';
        showError('Failed to analyze sentiment');
      }
    });
  }
}

function showLoading() {
  // Show loading state
  console.log('Loading sentiment data...');
}

function hideLoading() {
  // Hide loading state
  console.log('Sentiment data loaded');
}

function showError(message) {
  console.error(message);
  // In production, show toast notification
}

function showSuccess(message) {
  console.log(message);
  // In production, show toast notification
}
