import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// @ts-expect-error types
import compression from 'vite-plugin-compression';
// @ts-expect-error built-in types via node
import path from 'node:path';
// @ts-expect-error built-in types via node
import { fileURLToPath } from 'node:url';

// ESM __dirname polyfill
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), compression({ algorithm: 'brotliCompress', deleteOriginFile: false })],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
          vendor: ['axios', '@tanstack/react-query', 'recharts'],
        },
      },
    },
  },
}); 