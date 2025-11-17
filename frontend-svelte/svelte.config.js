import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/**
 * SvelteKit configuration for RAG Regulatory Analysis System
 * Includes TypeScript support, path aliases, and Vite preprocessing
 *
 * @type {import('@sveltejs/kit').Config}
 */
export default {
  // Use Vite preprocessor for TypeScript, PostCSS, and other features
  preprocess: vitePreprocess({
    typescript: true,
    postcss: true,
  }),

  kit: {
    // Use Vite adapter (default SvelteKit adapter)
    // env: {
    //   publicPrefix: 'PUBLIC_',
    // },

    // Path aliases for cleaner imports
    alias: {
      $lib: 'src/lib',
      $components: 'src/components',
      $pages: 'src/routes',
      $stores: 'src/lib/stores',
      $api: 'src/lib/api',
      $utils: 'src/lib/utils',
      $types: 'src/lib/types',
      $ws: 'src/lib/websocket',
    },

    // Disable SSR for client-side only application
    // ssr: false,

    // // Enable enhanced.dev for load functions and server hooks
    // version: {
    //   name: '1.0.0',
    //   pollInterval: 60000, // 1 minute
    // },
  },
};
