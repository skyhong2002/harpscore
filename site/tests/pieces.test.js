import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
const catalog = JSON.parse(readFileSync(new URL('../src/data/arrangements.json', import.meta.url), 'utf8'));

test('published pieces have HarpScore production evidence and unique edition previews', () => {
  const all = catalog.pieces.flatMap(piece => piece.editions);
  assert.equal(new Set(all.map(e => e.sha256)).size, all.length);
  assert.equal(new Set(all.map(e => e.image)).size, all.length);
  for (const piece of catalog.pieces) {
    assert.equal(piece.production, 'HarpScore');
    assert.ok(piece.editions.length > 0);
    for (const edition of piece.editions) {
      assert.match(edition.production_record_sha256, /^[a-f0-9]{64}$/);
      assert.match(edition.sha256, /^[a-f0-9]{64}$/);
      assert.ok(edition.filename.endsWith('.mscz'));
      assert.equal(edition.file, `https://github.com/skyhong2002/harpscore/releases/download/scores-2026-10-31/${encodeURIComponent(edition.filename)}`);
      assert.equal(edition.image, `/images/arrangements/${edition.id}.webp`);
      assert.match(edition.preview_sha256, /^[a-f0-9]{64}$/);
      const image = new URL(`../public${edition.image}`, import.meta.url);
      assert.ok(existsSync(image), `${piece.title}: ${edition.label}`);
      assert.doesNotMatch(edition.label, /Source_Imported/);
    }
  }
});

test('public catalog does not disclose local provenance paths or include raw imports', () => {
  assert.doesNotMatch(JSON.stringify(catalog), /\/Users\/|\/home\/|file:\/\/|Source_Imported|Library_Catalog/);
  assert.ok(catalog.pieces.every(p => p.license.includes('MIT')));
});
