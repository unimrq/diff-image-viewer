import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  base: '/',
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: '0.0.0.0', // 或 '0.0.0.0'
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // 后端 FastAPI 地址
        changeOrigin: true,
      },
      '/images': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/thumbnails': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/cache': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    }
  }
})
