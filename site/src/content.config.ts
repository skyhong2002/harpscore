import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// The handbook is the repository's canonical docs/ tree; the site never keeps a copy.
const docs = defineCollection({
  loader: glob({ pattern: '**/*.md', base: '../docs' }),
  schema: z.object({
    title: z.string(),
    order: z.number().default(99),
    summary: z.string().optional(),
  }),
});

// Each piece folder carries its own README next to piece.json.
const pieces = defineCollection({
  loader: glob({
    pattern: '*/README.md',
    base: '../pieces',
    generateId: ({ entry }) => entry.split('/')[0],
  }),
});

export const collections = { docs, pieces };
