// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';

// Static output, deployed to Vercel. No `base` path is needed here - that is a
// GitHub Pages concern, and setting one would break asset URLs on Vercel.
export default defineConfig({
  output: 'static',
  site: 'https://india-fs-pulse.vercel.app',
  integrations: [sitemap()],
  vite: { plugins: [tailwind()] },
  build: { inlineStylesheets: 'auto' },
});
