import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as E
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('templates',ROOT/'scripts/create_templates.py')
templates=importlib.util.module_from_spec(spec);spec.loader.exec_module(templates)

class TemplatesTest(unittest.TestCase):
    def test_starters_are_native_empty_and_self_contained(self):
        with tempfile.TemporaryDirectory() as d:
            records=templates.build_templates(d)
            self.assertEqual(len(records),8)
            for record in records:
                with zipfile.ZipFile(Path(d)/record['file']) as z:
                    self.assertIsNone(z.testzip())
                    container=E.fromstring(z.read('META-INF/container.xml'))
                    for item in container.findall('rootfiles/rootfile'):
                        self.assertIn(item.attrib['full-path'],z.namelist())
                    self.assertFalse(any(n.startswith(('Pictures/','audio/')) for n in z.namelist()))
                    root=E.fromstring(z.read(next(n for n in z.namelist()if n.endswith('.mscx'))))
                    self.assertEqual(len(root.findall('Score/Staff')),record['staves'])
                    self.assertFalse(root.findall('.//Note'))
                    for staff in root.findall('Score/Staff'):
                        self.assertEqual(len(staff.findall('Measure')),12)
                        for measure in staff.findall('Measure'):
                            self.assertEqual(measure.findtext('voice/Rest/duration'),'1/1')
                    self.assertNotIn(b'Summer',E.tostring(root))
                    self.assertNotIn(b'/Users/',E.tostring(root))

    def test_jianpu_and_staff_settings_are_not_confused(self):
        with tempfile.TemporaryDirectory() as d:
            records=templates.build_templates(d)
            for record in records:
                with zipfile.ZipFile(Path(d)/record['file'])as z:
                    root=E.fromstring(z.read(next(n for n in z.namelist()if n.endswith('.mscx'))))
                    is_j=record['notation']=='jianpu'
                    for staff in root.findall('Score/Staff'):
                        zeros=staff.findall("Measure/voice/StaffText[text='0']")
                        self.assertEqual(len(zeros),48 if is_j else 0)
                    style=E.fromstring(z.read('score_style.mss'))
                    self.assertEqual(style.findtext('Style/oddHeaderC'),'$:workTitle:')
                    self.assertEqual(style.findtext('Style/oddFooterC'),'$P / $n')
                    if is_j:
                        self.assertTrue(all(st.findtext('StaffType/invisible')=='1' for st in root.findall('Score/Part/Staff')))

    def test_rebuild_is_reproducible(self):
        with tempfile.TemporaryDirectory()as a,tempfile.TemporaryDirectory()as b:
            ra=templates.build_templates(a);rb=templates.build_templates(b)
            self.assertEqual([r['sha256']for r in ra],[r['sha256']for r in rb])

if __name__=='__main__':unittest.main()
