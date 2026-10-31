import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { getCollection, type CollectionEntry } from 'astro:content';
import { ROOT } from './rules.mjs';

export const REPO = 'https://github.com/skyhong2002/harpscore';
export const VERSION = readFileSync(join(ROOT, 'VERSION'), 'utf8').trim();

/** Prefix a site path with the deployment base ("/harpscore"). */
export function url(path = ''): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}/${path.replace(/^\//, '')}`;
}

// Folder order and labels for the handbook. A doc's folder is its section;
// top-level docs (e.g. maintaining.md) fall into "project".
export const SECTIONS = [
  { id: 'guide', label: '開始', blurb: '交付前的守則、從新曲開始的流程與 Summer 版式驗證。' },
  { id: 'rules', label: '規則', blurb: '配器、簡譜、來源核對與交付驗收的編號規則。' },
  { id: 'engraving', label: 'MuseScore 工法', blurb: '覆層、碰撞診斷與自適應部距的實作經驗。' },
  { id: 'history', label: '偏好與決策', blurb: '創始使用者的偏好，以及每次修正如何成為規則。' },
  { id: 'project', label: '專案', blurb: '這份 skill 如何維護與發布。' },
] as const;

export type Doc = CollectionEntry<'docs'>;

export function sectionOf(doc: Doc): string {
  return doc.id.includes('/') ? doc.id.split('/')[0] : 'project';
}

export function docHref(doc: Doc | string): string {
  return url(`docs/${typeof doc === 'string' ? doc : doc.id}/`);
}

export async function handbook() {
  const docs = await getCollection('docs');
  return SECTIONS.map((section) => ({
    ...section,
    docs: docs
      .filter((doc) => sectionOf(doc) === section.id)
      .sort((a, b) => a.data.order - b.data.order || a.id.localeCompare(b.id)),
  })).filter((section) => section.docs.length);
}

export interface Edition {
  id: string;
  ensemble: string;
  label: string;
  notation: string;
  file: string;
  image?: string;
  preview?: string;
  staves?: number;
  sha256?: string;
  status?: string;
  production_record_sha256?: string;
  preview_sha256?: string;
}

export interface Piece {
  id: string;
  title: string;
  composer: string;
  license: string;
  source?: { name: string; url: string };
  meter?: string;
  tempo?: string;
  bars?: number;
  summary?: string;
  cover?: { image: string; caption: string };
  verification?: string;
  editions: Edition[];
  catalogue?: boolean;
  production?: string;
}

const PIECES = join(ROOT, 'pieces');

export function pieces(): Piece[] {
  if (!existsSync(PIECES)) return [];
  const examples: Piece[] = readdirSync(PIECES)
    .filter((name) => existsSync(join(PIECES, name, 'piece.json')))
    .sort()
    .map((name) => JSON.parse(readFileSync(join(PIECES, name, 'piece.json'), 'utf8')));
  const catalogPath = join(ROOT, 'site/src/data/arrangements.json');
  if (!existsSync(catalogPath)) return examples;
  const catalog: Piece[] = JSON.parse(readFileSync(catalogPath, 'utf8')).pieces;
  const overrides = new Map(catalog.map(piece => [piece.id, piece]));
  return [
    ...examples.map(piece => {
      const entry = overrides.get(piece.id);
      if (!entry) return piece;
      return { ...piece, editions: piece.editions.map(edition => {
        const current = entry.editions.find(e => e.sha256 === edition.sha256);
        return current ? { ...edition, image: current.image, preview_sha256: current.preview_sha256, status: current.status } : edition;
      }) };
    }),
    ...catalog.filter(piece => !examples.some(example => example.id === piece.id))
      .sort((a, b) => a.title.localeCompare(b.title, 'zh-Hant')),
  ];
}

/** Public URL of a file inside a piece folder (piece files are published verbatim). */
export function pieceFile(piece: Piece, path: string): string {
  if (path.startsWith('https://')) return path;
  if (path.startsWith('/')) return url(path);
  return url(`pieces/${piece.id}/${path}`);
}

/** Group a piece's editions by ensemble, keeping manifest order. */
export function ensembles(piece: Piece) {
  const groups = new Map<string, Edition[]>();
  for (const edition of piece.editions) {
    groups.set(edition.ensemble, [...(groups.get(edition.ensemble) ?? []), edition]);
  }
  return [...groups.values()];
}

export const NOTATION_LABEL: Record<string, string> = {
  staff: '五線總譜',
  numbered: '簡譜總譜',
  'numbered-wind-and-staff-piano': '口琴簡譜＋鋼琴五線譜',
};
