import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    proxy: {
      '/api': {
        // Use 127.0.0.1 (not localhost): many hosts resolve localhost → ::1 first while
        // uvicorn binds 127.0.0.1 only, so the proxy would otherwise get connection refused.
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
