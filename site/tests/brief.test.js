import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { makeBrief, prompt } from '../src/lib/brief.js';

const base = { title: '原創練習', source: '原創素材', ensemble: 'duet', level: 'beginner-2-months', notation: ['jianpu'], pdf: false, piano: true };

test('duet has combined harp edition and optional piano master, no individual parts', () => {
  const brief = makeBrief(base);
  assert.deepEqual(brief.editions, ['combined-harmonicas', 'with-piano-master']);
  assert.equal(brief.pdf, false);
  assert.match(prompt(brief, '9.9.9'), /不另拆個別口琴分部/);
});

test('prompt names the given version', () => {
  assert.match(prompt(makeBrief(base), '9.9.9'), /HarpScore 9\.9\.9 /);
});

test('quintet ignores piano option', () => {
  assert.deepEqual(makeBrief({ ...base, ensemble: 'quintet' }).editions, ['combined-harmonicas']);
});

test('quartet uses two chromatics, bass and chord without extra piano', () => {
  const brief = makeBrief({ ...base, ensemble: 'quartet' });
  assert.deepEqual(brief.editions, ['combined-harmonicas']);
  assert.match(prompt(brief, '0'), /兩部半音階、DB H.、Chord/);
});

test('reject incomplete and unsupported requests', () => {
  assert.throws(() => makeBrief({ ...base, source: '' }));
  assert.throws(() => makeBrief({ ...base, notation: [] }));
  assert.throws(() => makeBrief({ ...base, ensemble: 'trio' }));
  assert.throws(() => makeBrief({ ...base, ensemble: 'toString' }));
});

test('user contents preserved without execution', () => {
  const brief = makeBrief({ ...base, title: '<script>test</script>', notes: '保留 332' });
  assert.equal(brief.title, '<script>test</script>');
  assert.match(prompt(brief, '0'), /保留 332/);
});

test('briefs have the same keys as the published example', () => {
  const example = JSON.parse(readFileSync(new URL('../../examples/brief.json', import.meta.url), 'utf8'));
  assert.deepEqual(Object.keys(makeBrief(base)).sort(), Object.keys(example).sort());
});
