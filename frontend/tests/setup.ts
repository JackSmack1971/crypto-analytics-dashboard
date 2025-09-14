import { afterAll, afterEach, beforeAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import { setupServer } from 'msw/node';
import '@testing-library/jest-dom/vitest';

// Initialize Mock Service Worker server to intercept network requests
export const server = setupServer();

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));

// Reset handlers and clean up the DOM after each test
afterEach(() => {
  server.resetHandlers();
  cleanup();
});

// Close server after tests finish
afterAll(() => server.close());
