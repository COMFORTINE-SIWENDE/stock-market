// Chart.js is loaded globally from CDN as window.Chart (UMD global)
// Do NOT import it — reference as `Chart` directly.

// Registry: Map<canvasId, Chart instance>
const _registry = new Map();

// Dark theme defaults applied to every chart
export const CHART_DEFAULTS = {
  backgroundColor: 'transparent',
  gridColor: '#1e1f2a',
  tickColor: '#9ca3af',
  legendColor: '#cbd5e1',
};

// Destroy existing chart instance before re-rendering (prevents canvas reuse errors)
export function destroyChart(id) {
  if (_registry.has(id)) {
    _registry.get(id).destroy();
    _registry.delete(id);
  }
  // no-op if id not found
}

export function createLineChart(id, labels, datasets, options = {}) {
  destroyChart(id);
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  const chart = new Chart(canvas, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: CHART_DEFAULTS.legendColor } },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: {
        y: { grid: { color: CHART_DEFAULTS.gridColor }, ticks: { color: CHART_DEFAULTS.tickColor } },
        x: { grid: { color: CHART_DEFAULTS.gridColor }, ticks: { color: CHART_DEFAULTS.tickColor } },
      },
      ...options,
    },
  });
  _registry.set(id, chart);
  return chart;
}

export function createBarChart(id, labels, datasets, options = {}) {
  destroyChart(id);
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  const chart = new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: CHART_DEFAULTS.legendColor } },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: {
        y: { grid: { color: CHART_DEFAULTS.gridColor }, ticks: { color: CHART_DEFAULTS.tickColor } },
        x: { grid: { color: CHART_DEFAULTS.gridColor }, ticks: { color: CHART_DEFAULTS.tickColor } },
      },
      ...options,
    },
  });
  _registry.set(id, chart);
  return chart;
}

export function createScatterChart(id, datasets, options = {}) {
  destroyChart(id);
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  const chart = new Chart(canvas, {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: CHART_DEFAULTS.legendColor } },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: {
        x: {
          title: { display: true, text: 'Confidence', color: CHART_DEFAULTS.tickColor },
          grid: { color: CHART_DEFAULTS.gridColor },
          ticks: { color: CHART_DEFAULTS.tickColor },
        },
        y: {
          title: { display: true, text: 'Predicted Price', color: CHART_DEFAULTS.tickColor },
          grid: { color: CHART_DEFAULTS.gridColor },
          ticks: { color: CHART_DEFAULTS.tickColor },
        },
      },
      ...options,
    },
  });
  _registry.set(id, chart);
  return chart;
}
