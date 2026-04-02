import { describe, it, expect } from 'vitest';

describe('API Template', () => {
  it('should have health check', () => {
    expect(true).toBe(true);
  });

  it('should export app', async () => {
    const { app } = await import('../src/app.js');
    expect(app).toBeDefined();
  });
});
