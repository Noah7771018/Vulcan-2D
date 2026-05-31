import { defineConfig } from 'vite'

// base: './' keeps asset paths relative so the built app also loads under
// Electron's file:// protocol (double-click desktop build).
export default defineConfig({
  base: './',
  server: { port: 5173 },
  build: {
    outDir: 'dist',
    target: 'es2022',
    sourcemap: true,
  },
})
