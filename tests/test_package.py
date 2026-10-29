from pathlib import Path
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package', ROOT/'scripts/package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


def references(path):
    """Markdown destinations are document-relative; code paths are skill-root-relative.

    Command arguments such as input.mscz and renderer-geometry.json describe
    user-created artifacts, not bundled references. Explicit directory paths
    and named entrypoint files describe the repository/installed skill.
    """
    text = path.read_text()
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
        link = link.split(' "', 1)[0].strip('<>')
        parsed = urlsplit(link)
        if parsed.scheme or not parsed.path:
            continue
        yield path.parent/unquote(parsed.path), link
    for code in re.findall(r'`([^`\n]+)`', text):
        refs = set(re.findall(r'(?<![\w/])(?:\.{1,2}/)*(?:docs|profiles|layouts|pieces|tools|plugins|examples|scripts|agents|site)/[\w./-]*', code))
        refs.update(re.findall(r'(?<![\w/])(?:\.{1,2}/)*(?:[\w.-]+/)+[\w.-]+\.(?:md|json|py|qml|mscz|mscx|mss|xml|png|svg|webp)\b', code))
        for ref in refs:
            root_relative = ref.split('/')[0] in package.SKILL_DIRS + ('scripts', 'site')
            yield (ROOT/ref if root_relative else path.parent/ref), ref
        for ref in re.findall(r'(?<![\w/])(?:SKILL\.md|AGENTS\.md|LICENSE|VERSION)(?![\w/])', code):
            yield ROOT/ref, ref
    # Shell examples include executable bundled scripts outside inline code.
    for ref in re.findall(r'^python3 ((?:tools|pieces|scripts)/[\w./-]+\.py)', text, re.M):
        yield ROOT/ref, ref


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.target = Path(cls.temp.name)/'dist'
        package.build(cls.target)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_downloads_include_canonical_docs_without_private_material(self):
        with zipfile.ZipFile(self.target/'downloads/agent-kit.zip') as z:
            for name in ['SKILL.md', 'AGENTS.md', 'LICENSE', 'VERSION']:
                self.assertEqual(z.read(name), (ROOT/name).read_bytes())
            for folder in package.SKILL_DIRS:
                for path in package.files_in(folder):
                    name = path.relative_to(ROOT).as_posix()
                    self.assertEqual(z.read(name), path.read_bytes())
            self.assertFalse(any(n.startswith(('scripts/', 'site/', 'web/')) for n in z.namelist()))
        with zipfile.ZipFile(self.target/'downloads/source.zip') as z:
            for name in z.namelist():
                self.assertTrue(package.included(Path(name)), name)
                self.assertNotIn(Path(name).suffix.lower(), ['.mp3', '.wav', '.pdf'])
                if name.endswith('.mscz'):
                    self.assertTrue(name.startswith('pieces/entertainer/scores/HarpScore_'))
                if Path(name).suffix.lower() not in ['.webp', '.png', '.jpg', '.jpeg', '.mscz', '.zip']:
                    self.assertNotRegex(z.read(name).decode(), r'/Users/[A-Za-z0-9_-]+/')
            self.assertIn('scripts/package.py', z.namelist())
            self.assertIn('VERSION', z.namelist())

    def test_download_reproducibility(self):
        paths = list((self.target/'downloads').glob('*.zip'))
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        package.build(self.target)
        self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_adaptive_tool_runs_from_extracted_skill(self):
        with tempfile.TemporaryDirectory() as folder:
            with zipfile.ZipFile(self.target/'downloads/harpscore-skill.zip') as z:
                z.extractall(folder)
            installed = Path(folder)/'harpscore'
            result = subprocess.run([sys.executable, 'tools/adaptive_staff_spacing.py', 'plan', '--help'],
                                    cwd=installed, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--clearance', result.stdout)
            self.assertTrue((installed/'plugins/HarpScoreGeometry/HarpScoreGeometry.qml').is_file())
            for path in [installed/'SKILL.md', installed/'AGENTS.md', *sorted((installed/'docs').rglob('*.md'))]:
                for resolved, ref in references(path):
                    # Root references in code samples use the installed skill root.
                    if resolved.is_relative_to(ROOT):
                        resolved = installed/resolved.relative_to(ROOT)
                    self.assertTrue(resolved.exists(), f'{path}: {ref}')

    def test_machine_document_is_independent_of_filesystem_order(self):
        before = (self.target/'llms-full.txt').read_bytes()
        original = Path.rglob
        def reverse(path, pattern):
            return iter(reversed(list(original(path, pattern))))
        with patch.object(Path, 'rglob', reverse):
            package.build(self.target)
        self.assertEqual(before, (self.target/'llms-full.txt').read_bytes())

    def test_manifest_lists_every_doc_in_section_and_frontmatter_order(self):
        manifest = package.doc_manifest()
        self.assertEqual({r['path'] for r in manifest},
                         {p.relative_to(ROOT).as_posix() for p in (ROOT/'docs').rglob('*.md')})
        for record in manifest:
            self.assertTrue(record['title'])
            self.assertTrue(record['summary'])
            self.assertIsInstance(record['order'], int)
        result = subprocess.run([sys.executable, str(ROOT/'scripts/package.py'), '--manifest'],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), manifest)

    def test_every_doc_is_reachable_from_entrypoints(self):
        docs = set((ROOT/'docs').rglob('*.md'))
        pending = [ROOT/'SKILL.md', ROOT/'AGENTS.md']
        seen = set()
        while pending:
            path = pending.pop().resolve()
            if path in seen:
                continue
            seen.add(path)
            for resolved, _ in references(path):
                resolved = resolved.resolve()
                if resolved.is_file() and resolved.suffix == '.md' and resolved not in seen:
                    pending.append(resolved)
        self.assertFalse(docs-seen, sorted(str(p.relative_to(ROOT)) for p in docs-seen))
        full = (self.target/'llms-full.txt').read_text()
        for path in docs:
            self.assertIn('# FILE: '+path.relative_to(ROOT).as_posix()+'\n', full)

    def test_every_relative_reference_resolves(self):
        for path in [ROOT/'SKILL.md', ROOT/'AGENTS.md', *sorted((ROOT/'docs').rglob('*.md'))]:
            for resolved, ref in references(path):
                self.assertTrue(resolved.exists(), f'{path.relative_to(ROOT)}: {ref}')

    def test_output_preserves_unowned_files_and_cleans_owned_stale_files(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target/'index.html').write_text('site owns this')
            (target/'downloads').mkdir()
            (target/'downloads/unrelated.zip').write_bytes(b'unrelated')
            package.build(target)
            (target/'old-doc.md').write_text('previous package output')
            journal = target/package.OWNERSHIP
            journal.write_text(json.dumps(json.loads(journal.read_text())+['old-doc.md']))
            package.build(target)
            self.assertEqual((target/'index.html').read_text(), 'site owns this')
            self.assertEqual((target/'downloads/unrelated.zip').read_bytes(), b'unrelated')
            self.assertFalse((target/'old-doc.md').exists())

    def test_template_download_contains_only_piece_sources_and_layouts(self):
        with zipfile.ZipFile(self.target/'downloads/harpscore-musescore-templates.zip') as z:
            self.assertIn('pieces/entertainer/piece.json', z.namelist())
            self.assertIn('pieces/entertainer/README.md', z.namelist())
            self.assertIn('layouts/summer/provenance.json', z.namelist())
            self.assertTrue(any(n.startswith('pieces/entertainer/scores/') for n in z.namelist()))
            self.assertTrue(any(n.startswith('pieces/entertainer/events/') for n in z.namelist()))
            self.assertFalse(any('/build/' in n or '/source/' in n for n in z.namelist()))


if __name__ == '__main__':
    unittest.main()
