// Turns canonical Markdown into a linked handbook:
// - "J08a · ..." paragraphs/list items become anchored rule blocks,
// - mentions such as V17 or J23–J24 link to their definition,
// - relative links to repository files resolve to site routes or raw files,
// - the leading h1 is dropped because pages render the title themselves.
import { dirname, relative, resolve, sep } from 'node:path';
import { DOCS, ROOT, RULE_ID, docId } from './rules.mjs';

const SKIP = new Set(['a', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']);

const text = (value) => ({ type: 'text', value });
const element = (tagName, properties, children) => ({ type: 'element', tagName, properties, children });

export function docRoute(base, id) {
  return `${base}/docs/${id}/`;
}

export default function rehypeHarpScore({ base, rules }) {
  return (tree, file) => {
    const source = file.path ?? file.history?.[0];
    const current = source?.startsWith(DOCS) ? docId(source) : undefined;

    const ruleHref = (id) => (rules[id] === current ? `#${id}` : `${docRoute(base, rules[id])}#${id}`);

    function resolveLink(href) {
      if (!source || /^([a-z]+:|#|\/)/i.test(href)) return href;
      const [path, hash = ''] = href.split('#');
      const target = resolve(dirname(source), path);
      const repoPath = relative(ROOT, target).split(sep).join('/');
      if (repoPath.startsWith('..')) return href;
      if (target.startsWith(DOCS + sep) && target.endsWith('.md')) {
        return docRoute(base, docId(target)) + (hash ? `#${hash}` : '');
      }
      const piece = repoPath.match(/^pieces\/([^/]+)\/README\.md$/);
      if (piece) return `${base}/pieces/${piece[1]}/${hash ? `#${hash}` : ''}`;
      // Other repository files are published verbatim at the same path.
      return `${base}/${repoPath}${hash ? `#${hash}` : ''}`;
    }

    function anchorDefinition(node) {
      // Loose list items wrap their text in <p>; the anchor still belongs on the <li>.
      const holder = node.tagName === 'li' && node.children[0]?.tagName === 'p' ? node.children[0] : node;
      const first = holder.children[0];
      if (first?.type !== 'text') return false;
      const match = first.value.match(/^([GWAJVD]\d{2,3}[a-z]?) · /);
      if (!match || !rules[match[1]]) return false;
      const id = match[1];
      node.properties.id = id;
      node.properties.className = [...(node.properties.className ?? []), 'rule'];
      first.value = first.value.slice(match[0].length);
      holder.children.unshift(
        element('a', { className: ['rule-id'], href: `#${id}`, ariaLabel: `規則 ${id} 的連結` }, [text(id)]),
        text(' '),
      );
      return true;
    }

    function linkMentions(value) {
      const parts = [];
      let last = 0;
      for (const match of value.matchAll(RULE_ID)) {
        if (!rules[match[1]]) continue;
        if (match.index > last) parts.push(text(value.slice(last, match.index)));
        parts.push(element('a', { className: ['rule-ref'], href: ruleHref(match[1]) }, [text(match[1])]));
        last = match.index + match[0].length;
      }
      if (!parts.length) return null;
      if (last < value.length) parts.push(text(value.slice(last)));
      return parts;
    }

    function walk(node) {
      if (node.type !== 'element' && node.type !== 'root') return;
      if (node.type === 'element') {
        if (node.tagName === 'a' && typeof node.properties.href === 'string') {
          node.properties.href = resolveLink(node.properties.href);
        }
        if (node.tagName === 'p' || node.tagName === 'li') anchorDefinition(node);
        if (SKIP.has(node.tagName)) return;
        if (node.tagName === 'table') {
          node.properties.className = [...(node.properties.className ?? []), 'table'];
        }
      }
      node.children = node.children.flatMap((child) => {
        if (child.type === 'text') return linkMentions(child.value) ?? [child];
        walk(child);
        return [child];
      });
    }

    // Pages print the frontmatter title; the file's own h1 is for raw readers.
    const firstElement = tree.children.findIndex((child) => child.type === 'element');
    if (tree.children[firstElement]?.tagName === 'h1') tree.children.splice(firstElement, 1);

    walk(tree);
  };
}
