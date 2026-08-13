import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // 用 127.0.0.1 而非 localhost：后端 uvicorn 绑定 --host 0.0.0.0（仅 IPv4），
      // 而 node 解析 localhost 时优先走 IPv6 的 ::1，导致 ECONNREFUSED ::1:8502
      '/api': 'http://127.0.0.1:8502',
      '/media': 'http://127.0.0.1:8502'
    }
  }
})
