import { AppState } from './state.js';

const BASE_URL = 'http://localhost:8000';

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (AppState.token !== null) {
    headers['Authorization'] = `Bearer ${AppState.token}`;
  }

  const options = { method, headers };
  if (body !== null) {
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, options);
  } catch {
    throw new ApiError(0, 'Network error — check your connection');
  }

  if (!response.ok) {
    if (response.status === 401) {
      AppState.setToken(null);
      AppState.setUser(null);
      window.location.hash = '#/login';
    }
    let data = {};
    try {
      data = await response.json();
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, data.error || 'An unexpected error occurred');
  }

  return response.json();
}

export async function get(path) { return request('GET', path); }
export async function post(path, body) { return request('POST', path, body); }

export const api = {
  auth: {
    register: (data) => post('/auth/register', data),
    login: (data) => post('/auth/login', data),
    logout: () => post('/auth/logout'),
    me: () => get('/auth/me'),
  },
  stocks: {
    price: (symbol) => get(`/stocks/${symbol}/price`),
    data: (symbol, start, end) => get(`/stocks/${symbol}/data?start=${start}&end=${end}`),
    indicators: (symbol, start, end) => {
      const q = start && end ? `?start=${start}&end=${end}` : '';
      return get(`/stocks/${symbol}/indicators${q}`);
    },
    collect: (symbols, days = 365) => post('/stocks/collect', { symbols, days }),
  },
  sentiment: {
    get: (symbol, start, end) => {
      const q = start && end ? `?start=${start}&end=${end}` : '';
      return get(`/sentiment/${symbol}${q}`);
    },
    analyze: (symbol) => post(`/sentiment/${symbol}/analyze`),
  },
  predictions: {
    get: (symbol, days = 1) => get(`/predictions/${symbol}?days=${days}`),
    train: (symbol) => post(`/predictions/${symbol}/train`),
    history: (symbol) => get(`/predictions/${symbol}/history`),
    backtest: (symbol) => get(`/predictions/${symbol}/backtest`),
  },
  symbols: {
    search: (query) => get(`/symbols/search?q=${encodeURIComponent(query)}`),
  },
  agent: {
    query: (text) => post('/agent/query', { query: text }),
  },
};
