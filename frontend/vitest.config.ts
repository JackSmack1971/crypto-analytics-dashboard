import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';

// Vitest configuration leveraging Vite's React plugin and TS path resolution
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: 'jsdom', // Simulate browser for React Testing Library
    globals: true,
    setupFiles: './tests/setup.ts',
    exclude: ['tests/e2e/**'],
    coverage: {
      reporter: ['text', 'lcov'],
    },
  },
});
