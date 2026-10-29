import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('spacing', ROOT/'scripts/adaptive_staff_spacing.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def annotation(track, x, baseline, offset, height=1, visible=True):
    return dict(type=54, track=track, text='3', visible=visible, oy=offset,
                box=dict(x=x, y=baseline+offset, bx=0, by=0, w=1, h=height))


def geometry():
    return dict(error=None, rows=[dict(page=0, system=0, measure=0, tick=0,
                measureBox=dict(x=0,y=0,w=10,h=15), events=[], annotations=[
                    annotation(0, 2, 10, 3), annotation(4, 2, 17, -4)])],
                spanners=[], otherSpanners=[])


def score(path, spacer=None, offset=None):
    root = ET.Element('museScore',version='4.50'); s=ET.SubElement(root,'Score')
    for i in range(2):
        part=ET.SubElement(s,'Part'); st=ET.SubElement(part,'Staff',id=str(i+1))
        ET.SubElement(ET.SubElement(st,'StaffType'),'lines').text='1'
        if i==1 and offset is not None:ET.SubElement(st,'distOffset').text=str(offset)
    for i in range(2):
        st=ET.SubElement(s,'Staff',id=str(i+1)); bar=ET.SubElement(st,'Measure')
        if i==1 and spacer is not None:ET.SubElement(bar,'vspacerUp').text=str(spacer)
        v=ET.SubElement(bar,'voice'); chord=ET.SubElement(v,'Chord')
        ET.SubElement(chord,'durationType').text='whole'
        note=ET.SubElement(chord,'Note');ET.SubElement(note,'pitch').text='60'
        ET.SubElement(note,'velocity').text='83'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('score.mscx',ET.tostring(root));z.writestr('score_style.mss',b'unchanged style')
        z.writestr('audio-settings.json',b'{"keep":true}')


class SpacingTests(unittest.TestCase):
    def test_only_overlapping_ink_requires_space(self):
        g=geometry();targets,systems=m.propose(g,1,2,7,.35)
        self.assertEqual(targets,{0:8.35})
        g['rows'][0]['annotations'][1]['box']['x']=5
        self.assertEqual(m.propose(g,1,2,7,.35)[0],{})
        self.assertEqual(systems[0]['current_sp'],7)

    def test_translation_and_expansion_do_not_accumulate(self):
        g=geometry(); expected=m.propose(g,1,2,7,.35)[0]
        for a in g['rows'][0]['annotations']:a['box']['y']+=100
        g['rows'][0]['annotations'][1]['box']['y']+=4
        self.assertEqual(m.propose(g,1,2,7,.35)[0],expected)

    def test_pages_and_hidden_text_are_isolated(self):
        g=geometry();r=copy.deepcopy(g['rows'][0]);r.update(page=1,measure=1)
        r['annotations'][0]['box']['x']=8;g['rows'].append(r)
        self.assertEqual(m.propose(g,1,2,7,.35)[0],{0:8.35})
        g['rows'][0]['annotations'][0]['visible']=False
        # Hidden label cannot define a baseline; retain a visible normal numeral.
        g['rows'][0]['annotations'].append(annotation(0,8,10,0))
        self.assertEqual(m.propose(g,1,2,7,.35)[0],{})

    def test_cross_measure_line_and_duplicate_ticks(self):
        g=geometry();r=g['rows'][0];r['annotations'][1]['box']['y']=17;r['annotations'][1]['oy']=0
        other=copy.deepcopy(r);other.update(measure=1);other['measureBox']['x']=10
        other['annotations'][0]['box']['x']=12;g['rows'].append(other)
        g['otherSpanners']=[dict(track=4,visible=True,segments=[dict(system=0,
                                box=dict(x=1,y=12,w=15,h=.1))])]
        self.assertEqual(m.propose(g,1,2,7,.35)[0],{0:9.35,1:9.35})

    def test_bad_or_incomplete_geometry_fails(self):
        for change in [{'error':'failed'}, {'rows':[]}, {'coordinateUnits':'pixels'}]:
            g=geometry();g.update(change)
            with self.assertRaises(ValueError):m.propose(g,1,2,7,.35)
        g=geometry();g['rows'][0]['annotations'].append(annotation(0,2,13,0))
        with self.assertRaises(ValueError):m.propose(g,1,2,7,.35)

    def test_apply_preserves_music_archive_and_manual_spacing(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);src=p/'in.mscz';score(src,spacer=10)
            gp=p/'g.json';gp.write_text(json.dumps(geometry()))
            plan=m.make_plan(src,gp,1,2,7,.35);result=m.apply_plan(src,plan,p/'out.mscz')
            self.assertEqual(result['preserved_manual_spacer_measures'],[1])
            before,_,a=m.read_score(src);after,_,b=m.read_score(p/'out.mscz')
            self.assertEqual(before['audio-settings.json'],after['audio-settings.json'])
            self.assertEqual(before['score_style.mss'],after['score_style.mss'])
            self.assertEqual([ET.tostring(v)for v in a.iter('voice')],[ET.tostring(v)for v in b.iter('voice')])
            self.assertEqual(b.findtext('Score/Staff[2]/Measure/vspacerUp'),'10')

    def test_owned_spacing_shrinks_but_hand_edits_remain(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);src=p/'in.mscz';score(src);gp=p/'g.json';gp.write_text(json.dumps(geometry()))
            plan=m.make_plan(src,gp,1,2,7,.35);m.apply_plan(src,plan,p/'one.mscz')
            g=geometry();g['rows'][0]['annotations'][1]['box']['x']=5;gp.write_text(json.dumps(g))
            plan=m.make_plan(p/'one.mscz',gp,1,2,7,.35);m.apply_plan(p/'one.mscz',plan,p/'two.mscz')
            self.assertIsNone(m.read_score(p/'two.mscz')[2].find('Score/Staff[2]/Measure/vspacerUp'))
            files,n,r=m.read_score(p/'one.mscz');r.find('Score/Staff[2]/Measure/vspacerUp').text='12'
            files[n]=ET.tostring(r)
            with zipfile.ZipFile(p/'edited.mscz','w') as z:
                for name,data in files.items():z.writestr(name,data)
            plan=m.make_plan(p/'edited.mscz',gp,1,2,7,.35)
            result=m.apply_plan(p/'edited.mscz',plan,p/'three.mscz')
            self.assertEqual(result['preserved_manual_spacer_measures'],[1])
            self.assertEqual(m.read_score(p/'three.mscz')[2].findtext('Score/Staff[2]/Measure/vspacerUp'),'12')

    def test_stale_plan_overwrite_and_global_offset_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);src=p/'in.mscz';score(src,offset=1.1);gp=p/'g.json';gp.write_text(json.dumps(geometry()))
            with self.assertRaises(ValueError):m.make_plan(src,gp,1,2,7,.35)
            plan=m.make_plan(src,gp,1,2,7,.35,True)
            with self.assertRaises(ValueError):m.apply_plan(src,plan,src)
            m.apply_plan(src,plan,p/'out.mscz')
            self.assertIsNone(m.read_score(p/'out.mscz')[2].find('Score/Part[2]/Staff/distOffset'))
            with self.assertRaises(ValueError):m.apply_plan(src,plan,p/'out.mscz')
            score(src,offset=2)
            with self.assertRaises(ValueError):m.apply_plan(src,plan,p/'new.mscz')

    def test_standalone_cli(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/adaptive_staff_spacing.py'),'--help'],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
