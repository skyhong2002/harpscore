// Rule IDs (G/W/A/J/V/D + two digits + optional letter) are the shared
// vocabulary between docs, profiles and the decision ledger. This module is
// plain Node so both astro.config and pages can read it.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, resolve, sep } from 'node:path';

// Astro bundles this module before running it, so import.meta.url does not
// point at site/src/lib. The site is always built from site/.
export const ROOT = resolve(process.cwd(), '..');
export const DOCS = join(ROOT, 'docs');

export const RULE_ID = /\b([GWAJVD]\d{2}[a-z]?)\b/g;
// A definition is a paragraph or list item that opens with "ID · ".
const DEFINITION = /^(?:- )?([GWAJVD]\d{2}[a-z]?) · (.*)$/;

function markdownFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return markdownFiles(path);
    return name.endsWith('.md') ? [path] : [];
  });
}

/** "rules/jianpu.md" -> "rules/jianpu" — the same id Astro's glob loader gives the entry. */
export function docId(path) {
  return relative(DOCS, path).split(sep).join('/').replace(/\.md$/, '');
}

function stripFrontmatter(text) {
  return text.replace(/^---\n[\s\S]*?\n---\n/, '');
}

/** Every defined rule: { id, doc, text } in document order. */
export function rules() {
  return markdownFiles(DOCS).sort().flatMap((path) =>
    stripFrontmatter(readFileSync(path, 'utf8'))
      .split('\n')
      .map((line) => line.match(DEFINITION))
      .filter(Boolean)
      .map(([, id, text]) => ({ id, doc: docId(path), text })),
  );
}

/** Map of rule ID -> doc id, used to turn mentions into links. */
export function ruleIndex() {
  return Object.fromEntries(rules().map(({ id, doc }) => [id, doc]));
}
