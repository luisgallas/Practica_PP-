import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, strictPort: true, proxy: { '/api': process.env.HOSPEDA_API_PROXY || 'http://127.0.0.1:8000', '/media': process.env.HOSPEDA_API_PROXY || 'http://127.0.0.1:8000', '/admin': process.env.HOSPEDA_API_PROXY || 'http://127.0.0.1:8000', '/static': process.env.HOSPEDA_API_PROXY || 'http://127.0.0.1:8000' } },
  build: { rollupOptions: { output: { manualChunks: { react: ['react', 'react-dom', 'react-router-dom'], consultas: ['@tanstack/react-query', 'axios'] } } } },
  test: { environment: 'jsdom', setupFiles: './src/pruebas/preparacion.ts', css: false },
})
