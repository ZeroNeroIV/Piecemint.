import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Browser → same-origin /api → backend (see src/lib/apiBase.ts default in dev).
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
