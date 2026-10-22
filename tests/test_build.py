from pathlib import Path
import hashlib
import importlib.util
import json
import re
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build',ROOT/'scripts/build.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)

class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): build.build()

    def test_downloads_include_canonical_docs_without_private_material(self):
        with zipfile.ZipFile(ROOT/'dist/downloads/agent-kit.zip') as z:
            for name,_ in build.DOCS:
                self.assertEqual(z.read(f'docs/{name}.md'),(ROOT/f'docs/{name}.md').read_bytes())
        with zipfile.ZipFile(ROOT/'dist/downloads/source.zip') as z:
            for n in z.namelist():
                self.assertFalse(n.startswith(('.git/','.openai/','dist/')))
                self.assertNotIn(Path(n).suffix.lower(),['.mp3','.wav','.pdf'])
                if n.endswith('.mscz'):
                    self.assertTrue(n.startswith('templates/musescore/HarpScore_'))
                if Path(n).suffix.lower() not in ['.webp','.png','.jpg','.jpeg','.mscz']:
                    self.assertNotRegex(z.read(n).decode(),r'/Users/[A-Za-z0-9_-]+/')

    def test_download_reproducibility(self):
        paths=list((ROOT/'dist/downloads').glob('*.zip'))
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        build.build()
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_machine_document_is_independent_of_filesystem_order(self):
        before=(ROOT/'dist/llms-full.txt').read_bytes()
        original=Path.glob
        def reverse_profiles(path,pattern):
            values=list(original(path,pattern))
            return iter(reversed(values)) if path==ROOT/'profiles' and pattern=='*.json' else iter(values)
        with patch.object(Path,'glob',reverse_profiles):build.build()
        self.assertEqual(before,(ROOT/'dist/llms-full.txt').read_bytes())

    def test_static_references_resolve(self):
        for ref in re.findall(r'(?:href|src)="([^"]+)"',(ROOT/'dist/index.html').read_text()):
            if not ref.startswith(('#','https://','http://')):self.assertTrue((ROOT/'dist'/ref).is_file(),ref)

    def test_browser_assets_use_content_versioned_urls(self):
        refs=re.findall(r'(?:href|src)="([^"/]+\.(?:js|css))"',(ROOT/'dist/index.html').read_text())
        self.assertEqual(len(refs),4)
        for ref in refs:
            name,digest,suffix=ref.rsplit('.',2)
            data=(ROOT/'dist'/ref).read_bytes()
            self.assertEqual(digest,hashlib.sha256(data).hexdigest()[:12])
            self.assertEqual(data,(ROOT/'dist'/f'{name}.{suffix}').read_bytes())

    def test_renderer_escapes_source_text(self):
        self.assertIn('&lt;script&gt;',build.render('<script>alert(1)</script>'))
        self.assertNotIn('<script>',build.render('<script>alert(1)</script>'))

    def test_skill_references_are_bundled(self):
        with zipfile.ZipFile(ROOT/'dist/downloads/harpscore-skill.zip') as z:
            for name in re.findall(r'`((?:docs|profiles|scripts)/[\w./-]+\.(?:md|json|py))`',z.read('harpscore/SKILL.md').decode()):
                self.assertIn('harpscore/'+name,z.namelist())
            self.assertNotIn('harpscore/scripts/tryout.py',z.namelist())
        self.assertFalse((ROOT/'dist/downloads/harpscore-trial.zip').exists())

if __name__=='__main__':unittest.main()
