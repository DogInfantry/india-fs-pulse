// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Static output, deployed to Vercel. No `base` path is needed here: that is a
// GitHub Pages concern, and setting one would break asset URLs on Vercel.
export default defineConfig({
  output: 'static',
  site: 'https://india-fs-pulse.vercel.app',
  // vercel.json sets cleanUrls with trailingSlash false, so the sitemap must
  // agree or every non-root URL it lists answers with a 308.
  trailingSlash: 'never',
  integrations: [sitemap()],
  build: { inlineStylesheets: 'auto' },
});
