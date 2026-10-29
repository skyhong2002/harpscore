// Every same-site href/src in the built site must point at a published file.
// Run after `npm run build`; skipped when there is no build output yet.
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const DIST = new URL('../dist/', import.meta.url).pathname;
const BASE = '/harpscore/';

function pages(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return pages(path);
    return name.endsWith('.html') ? [path] : [];
  });
}

test('internal links resolve in the built site', { skip: !existsSync(join(DIST, 'index.html')) }, () => {
  const broken = new Set();
  for (const page of pages(DIST)) {
    for (const [, ref] of readFileSync(page, 'utf8').matchAll(/(?:href|src)="([^"#?]+)/g)) {
      if (!ref.startsWith(BASE)) continue;
      const path = join(DIST, decodeURIComponent(ref.slice(BASE.length)));
      if (!existsSync(path) || (statSync(path).isDirectory() && !existsSync(join(path, 'index.html')))) {
        broken.add(`${page.slice(DIST.length)} -> ${ref}`);
      }
    }
  }
  assert.deepEqual([...broken], []);
});

test('downloads and agent files are published', { skip: !existsSync(join(DIST, 'index.html')) }, () => {
  for (const file of ['SKILL.md', 'llms.txt', 'llms-full.txt', 'downloads/harpscore-skill.zip', 'downloads/source.zip']) {
    assert.ok(existsSync(join(DIST, file)), file);
  }
});
