import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as E
from fractions import Fraction

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('trial',ROOT/'scripts/tryout.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)

class TrialTests(unittest.TestCase):
    def test_measures_and_chord_timing_survive_musicxml(self):
        with tempfile.TemporaryDirectory() as d:
            payload=trial.write_fixture(d);xml=E.parse(Path(d)/'original.musicxml')
            self.assertEqual(len(xml.findall('part')),2)
            for part in xml.findall('part'):
                for measure in part.findall('measure'):
                    self.assertEqual(sum(int(n.findtext('duration')) for n in measure.findall('note') if n.find('chord') is None),16)
            first=xml.findall('part')[1].find('measure');at=0;harmonies=[]
            for item in first:
                if item.tag=='harmony':harmonies.append((at,item.findtext('root/root-step')))
                if item.tag=='note' and item.find('chord') is None:at+=int(item.findtext('duration'))
            self.assertEqual(harmonies,[(0,'C'),(8,'G')])
            self.assertEqual(json.loads((Path(d)/'events.json').read_text()),payload)

    def test_syncopation_ties_and_duration_not_modified(self):
        with tempfile.TemporaryDirectory() as d:
            trial.write_fixture(d);xml=E.parse(Path(d)/'original.musicxml')
            m=xml.find("part[@id='P1']/measure[@number='3']")
            ties=[(n.findtext('pitch/step'),n.find('tie').attrib['type'],n.findtext('duration')) for n in m.findall('note') if n.find('tie') is not None]
            self.assertEqual(ties,[('F','start','2'),('F','stop','2')])
            notes=trial.event_rows()[0]['measures'][2]
            self.assertEqual(notes[2]['duration'],'1')

if __name__=='__main__':unittest.main()
