import { defineConfig } from 'astro/config';
import { unified } from '@astrojs/markdown-remark';
import { ruleIndex } from './src/lib/rules.mjs';
import rehypeHarpScore from './src/lib/rehype-harpscore.mjs';

const base = '/harpscore';

export default defineConfig({
  site: 'https://skyhong2002.github.io',
  base,
  trailingSlash: 'always',
  build: { format: 'directory' },
  markdown: {
    processor: unified({
      rehypePlugins: [[rehypeHarpScore, { base, rules: ruleIndex() }]],
    }),
  },
});
