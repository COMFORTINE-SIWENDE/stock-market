// AppState singleton — central source of truth for the app

const _subscribers = [];

const AppState = {
  currentSymbol: 'SCOM.NR',
  currentUser: null,
  token: null,
  priceData: [],
  sentimentData: [],
  predictions: [],
  activeRoute: '/dashboard',

  setSymbol(symbol) {
    this.currentSymbol = symbol;
    for (const cb of _subscribers) {
      cb(symbol);
    }
  },

  subscribe(callback) {
    _subscribers.push(callback);
    return () => {
      const idx = _subscribers.indexOf(callback);
      if (idx !== -1) _subscribers.splice(idx, 1);
    };
  },

  setToken(token) {
    if (token !== null) {
      localStorage.setItem('mm_token', token);
      this.token = token;
    } else {
      localStorage.removeItem('mm_token');
      this.token = null;
    }
  },

  setUser(user) {
    this.currentUser = user;
  },
};

// Initialize token from localStorage if present
const _stored = localStorage.getItem('mm_token');
if (_stored) {
  AppState.token = _stored;
}

// Make AppState globally available
window.AppState = AppState;
