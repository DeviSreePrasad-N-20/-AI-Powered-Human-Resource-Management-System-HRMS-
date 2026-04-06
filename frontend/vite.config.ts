import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/dashboard': 'http://127.0.0.1:8000',
      '/analytics': 'http://127.0.0.1:8000',
      '/employees': 'http://127.0.0.1:8000',
      '/recruitment': 'http://127.0.0.1:8000',
      '/leave': 'http://127.0.0.1:8000',
      '/performance': 'http://127.0.0.1:8000',
      '/onboarding': 'http://127.0.0.1:8000',
      '/uploads': 'http://127.0.0.1:8000',
    },
  },
})
