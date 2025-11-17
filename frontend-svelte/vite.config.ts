/**
 * Vite configuration for RAG Regulatory Analysis System
 * Includes Svelte plugin, TypeScript, environment variables, and optimizations
 */

import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

export default defineConfig({
  plugins: [
    svelte({
      // Enable CSS scope resolution in inline component styles
      emitCss: true,
      // Compile mode can be either "legacy" or "modern"
      compilerOptions: {
        customElement: false,
      },
    }),
  ],

  resolve: {
    // Path aliases matching svelte.config.js
    alias: {
      $lib: path.resolve('./src/lib'),
      $components: path.resolve('./src/components'),
      $pages: path.resolve('./src/routes'),
      $stores: path.resolve('./src/lib/stores'),
      $api: path.resolve('./src/lib/api'),
      $utils: path.resolve('./src/lib/utils'),
      $types: path.resolve('./src/lib/types'),
      $ws: path.resolve('./src/lib/websocket'),
    },
  },

  server: {
    port: 5173,
    strictPort: false,
    host: 'localhost',
    // Proxy API requests to backend
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        // Remove /api prefix when forwarding to backend
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
      '/health': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    target: 'ES2020',
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV === 'development',
    minify: 'terser',
    rollupOptions: {
      output: {
        // Optimize code splitting for better caching
        manualChunks: {
          'vendor-svelte': ['svelte'],
          'vendor-ui': ['highlight.js', 'mammoth', 'marked'],
        },
      },
    },
  },

  // Environment variable handling
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },

  // Optimize dependencies
  optimizeDeps: {
    include: [
      'highlight.js',
      'mammoth',
      'marked',
      'socket.io-client',
    ],
    exclude: ['svelte'],
  },

  // CSS preprocessing
  css: {
    postcss: './postcss.config.js',
    preprocessorOptions: {
      scss: {
        // If using SCSS
      },
    },
  },

  // Esbuild options for improved output
  esbuild: {
    target: 'ES2020',
    keepNames: true,
    mangleCache: {},
  },
});
