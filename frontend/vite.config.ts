/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    open: false,
    proxy: { '/api': 'http://localhost:8000' },
  },
  build: {
    manifest: true,
    rollupOptions: {
      output: {
        onlyExplicitManualChunks: true,
        manualChunks: (id) => /node_modules\/(recharts|d3-[^/]+|victory-vendor)\//.test(id) ? 'recharts' : undefined,
      },
    },
  },
  test: {
    maxWorkers: 2,
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setupTests.ts',
    css: false,
  },
});
