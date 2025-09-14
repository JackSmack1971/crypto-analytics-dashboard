import { http, HttpResponse } from 'msw';
import { server } from '../setup';

// Simple function that calls the backend health endpoint
async function getHealth() {
  const res = await fetch('/api/health');
  if (!res.ok) throw new Error('Network response was not ok');
  return res.json();
}

describe('health API', () => {
  it('returns mocked health status', async () => {
    server.use(
      http.get('/api/health', () => HttpResponse.json({ status: 'ok' })),
    );
    await expect(getHealth()).resolves.toEqual({ status: 'ok' });
  });
});
