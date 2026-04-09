import { describe, it, expect, beforeEach } from 'vitest';

// Reset module state between tests by clearing localStorage and re-importing
// We use a fresh import per describe block via dynamic import with cache-busting

describe('AppState — initial values', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('has correct default field values', async () => {
    // Re-import to get a fresh module evaluation with empty localStorage
    const { AppState } = await import('../frontend/js/state.js?v=init');
    expect(AppState.currentSymbol).toBe('AAPL');
    expect(AppState.currentUser).toBeNull();
    expect(AppState.priceData).toEqual([]);
    expect(AppState.sentimentData).toEqual([]);
    expect(AppState.predictions).toEqual([]);
    expect(AppState.activeRoute).toBe('/dashboard');
  });

  it('reads mm_token from localStorage on init', async () => {
    localStorage.setItem('mm_token', 'test-jwt-token');
    const { AppState } = await import('../frontend/js/state.js?v=token-init');
    expect(AppState.token).toBe('test-jwt-token');
  });

  it('token is null when localStorage has no mm_token', async () => {
    localStorage.removeItem('mm_token');
    const { AppState } = await import('../frontend/js/state.js?v=no-token');
    expect(AppState.token).toBeNull();
  });
});

describe('AppState — setToken', () => {
  it('writes token to localStorage and updates this.token', async () => {
    localStorage.clear();
    const { AppState } = await import('../frontend/js/state.js?v=set-token');
    AppState.setToken('my-jwt');
    expect(AppState.token).toBe('my-jwt');
    expect(localStorage.getItem('mm_token')).toBe('my-jwt');
  });

  it('setToken(null) removes mm_token from localStorage and sets token to null', async () => {
    localStorage.setItem('mm_token', 'existing-token');
    const { AppState } = await import('../frontend/js/state.js?v=clear-token');
    AppState.setToken(null);
    expect(AppState.token).toBeNull();
    expect(localStorage.getItem('mm_token')).toBeNull();
  });
});

describe('AppState — setUser', () => {
  it('updates currentUser', async () => {
    const { AppState } = await import('../frontend/js/state.js?v=set-user');
    const user = { id: 1, username: 'alice', email: 'alice@example.com' };
    AppState.setUser(user);
    expect(AppState.currentUser).toEqual(user);
  });

  it('setUser(null) clears currentUser', async () => {
    const { AppState } = await import('../frontend/js/state.js?v=clear-user');
    AppState.setUser({ id: 1 });
    AppState.setUser(null);
    expect(AppState.currentUser).toBeNull();
  });
});

describe('AppState — subscribe / setSymbol', () => {
  it('subscribe callback is called when setSymbol is invoked', async () => {
    const { AppState } = await import('../frontend/js/state.js?v=subscribe');
    const received = [];
    AppState.subscribe(sym => received.push(sym));
    AppState.setSymbol('TSLA');
    expect(received).toContain('TSLA');
  });

  it('unsubscribe removes the callback', async () => {
    const { AppState } = await import('../frontend/js/state.js?v=unsub');
    const received = [];
    const unsub = AppState.subscribe(sym => received.push(sym));
    unsub();
    AppState.setSymbol('GOOG');
    expect(received).toHaveLength(0);
  });
});
