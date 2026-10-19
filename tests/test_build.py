from pathlib import Path
import hashlib
import importlib.util
import json
import re
import unittest
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
                self.assertNotIn(Path(n).suffix.lower(),['.mscz','.mp3','.wav','.pdf'])
                self.assertNotRegex(z.read(n).decode(),r'/Users/[A-Za-z0-9_-]+/')

    def test_download_reproducibility(self):
        paths=list((ROOT/'dist/downloads').glob('*.zip'))
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        build.build()
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_static_references_resolve(self):
        for ref in re.findall(r'(?:href|src)="([^"]+)"',(ROOT/'dist/index.html').read_text()):
            if not ref.startswith('#'):self.assertTrue((ROOT/'dist'/ref).is_file(),ref)

    def test_renderer_escapes_source_text(self):
        self.assertIn('&lt;script&gt;',build.render('<script>alert(1)</script>'))
        self.assertNotIn('<script>',build.render('<script>alert(1)</script>'))

    def test_skill_references_are_bundled(self):
        with zipfile.ZipFile(ROOT/'dist/downloads/harmonica-arranging-skill.zip') as z:
            for name in re.findall(r'references/([\w.-]+)',z.read('harmonica-arranging/SKILL.md').decode()):
                self.assertIn('harmonica-arranging/references/'+name,z.namelist())

if __name__=='__main__':unittest.main()
