import { describe, it, expect } from 'vitest';

describe('smoke test', () => {
  it('environment boots correctly', () => {
    expect(1 + 1).toBe(2);
  });
});
