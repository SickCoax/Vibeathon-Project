import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const backendUrl = process.env.VIBESHIFT_BACKEND_URL ?? 'http://127.0.0.1:5001';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: false,
      },
    },
  },
});
