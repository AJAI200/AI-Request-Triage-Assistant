import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/triage': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      }
    }
  }
})
