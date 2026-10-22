import importlib.util
import json
from fractions import Fraction as F
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as E
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('templates',ROOT/'scripts/create_templates.py')
templates=importlib.util.module_from_spec(spec);spec.loader.exec_module(templates)

DURATIONS={'whole':F(4),'half':F(2),'quarter':F(1),'eighth':F(1,2),'16th':F(1,4)}

def read_score(path):
    with zipfile.ZipFile(path) as z:
        return E.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.mscx'))))

def read_bar(voice):
    """Independent native timeline reader, including tied continuations."""
    t=F(0);events=[]
    for n in voice:
        if n.tag=='location':t+=F(n.findtext('fractions','0'))*4
        elif n.tag in ['Chord','Rest']:
            d=DURATIONS[n.findtext('durationType')]*(2-F(1,2**int(n.findtext('dots','0'))))
            pitches=[int(p.findtext('pitch')) for p in n.findall('Note')]
            velocities=[int(p.findtext('velocity')) for p in n.findall('Note')]
            tied=n.find("Note/Spanner[@type='Tie']/prev") is not None
            if tied:
                assert events and events[-1]['pitches']==pitches
                assert events[-1]['onset']+events[-1]['duration']==t
                assert events[-1]['velocities']==velocities
                events[-1]['duration']+=d
            else:events.append(dict(onset=t,duration=d,pitches=pitches,velocities=velocities))
            t+=d
    return t,events

class TemplatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.dest=Path(cls.temp.name)
        cls.records=templates.build_templates(cls.dest,forms=list(templates.EDITIONS))

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_musescore_locations_always_use_explicit_denominators(self):
        # Fraction('-2') is valid Python but MuseScore reads that bare XML
        # integer as -2/1024. Audit serialized output, not our Python reader.
        for record in self.records:
            root=read_score(self.dest/record['file'])
            for node in root.findall('.//location/fractions'):
                self.assertRegex(node.text or '',r'^-?\d+/[1-9]\d*$')
        from entertainer_notation import loc
        for beats,expected in [(4,'1/1'),(-8,'-2/1'),(0,'0/1'),(F(1,2),'1/8')]:
            self.assertEqual(loc(beats).findtext('fractions'),expected)

    def test_eight_native_examples_have_public_domain_theme(self):
        self.assertEqual(len(self.records),9)
        for record in self.records:
            with zipfile.ZipFile(self.dest/record['file']) as z:
                self.assertIsNone(z.testzip())
                for item in E.fromstring(z.read('META-INF/container.xml')).findall('rootfiles/rootfile'):
                    self.assertIn(item.attrib['full-path'],z.namelist())
                self.assertFalse(any(n.startswith(('Pictures/','audio/')) for n in z.namelist()))
            root=read_score(self.dest/record['file'])
            self.assertEqual(len(root.findall('Score/Staff')),record['staves'])
            for staff in root.findall('Score/Staff'):
                self.assertEqual(len(staff.findall('Measure')),152)
                self.assertGreater(len(staff.findall('.//Note')),10)
            self.assertNotIn(b'Summer',E.tostring(root));self.assertNotIn(b'/Users/',E.tostring(root))
            self.assertNotIn('Jianpu',record['file'])

    def test_native_playback_equals_authoritative_events_in_both_notations(self):
        from entertainer import midi
        for record in self.records+templates.build_templates(self.dest,forms=['Quartet']):
            root=read_score(self.dest/record['file'])
            source=json.loads((self.dest/'events'/f"{record['form']}.json").read_text())
            for staff,part in zip(root.findall('Score/Staff'),source['parts']):
                actual=[];want=[];base=F(0);last={};previous={}
                for mi,(measure,length)in enumerate(zip(staff.findall('Measure'),source['measure_beats'])):
                    for vi,voice in enumerate(measure.findall('voice')):
                        t=F(0)
                        for n in voice:
                            if n.tag=='location':t+=F(n.findtext('fractions','0'))*4
                            elif n.tag in ['Chord','Rest']:
                                d=DURATIONS[n.findtext('durationType')]*(2-F(1,2**int(n.findtext('dots','0'))))
                                for note in n.findall('Note'):
                                    p=int(note.findtext('pitch'));velocity=int(note.findtext('velocity'));key=(vi,p)
                                    if note.find("Spanner[@type='Tie']/prev")is not None:
                                        old=last[key];self.assertEqual(old[1],base+t);old[1]+=d
                                    else:
                                        e=[base+t,base+t+d,p,velocity];actual.append(e);last[key]=e
                                t+=d
                        self.assertEqual(t,F(length))
                    for vi,rows in enumerate([part['measures']]+part.get('additional_voices',[])):
                        for e in rows[mi]:
                            for pitch in e['pitches']:
                                p=midi(pitch);a=base+F(e['onset']);b=a+F(e['duration']);key=(vi,p)
                                if e['tie_in']:
                                    old=previous[key];self.assertEqual(old[1],a);old[1]=b
                                else:
                                    item=[a,b,p,e['velocity']];want.append(item);previous[key]=item
                    base+=F(length)
                self.assertEqual(sorted(actual),sorted(want),(record['file'],part['role']))

    def test_overlay_rhythm_accidentals_and_chord_lanes(self):
        root=read_score(self.dest/'HarpScore_Quintet_Numbered.mscz')
        for voice in root.findall('Score/Staff/Measure/voice'):
            t=F(0)
            for n in voice:
                if n.tag=='location':t+=F(n.findtext('fractions','0'))*4
                if n.tag=='Spanner' and n.find('TextLine') is not None:
                    end=t+F(n.findtext('next/location/fractions'))*4
                    self.assertEqual(int(t/2),int(end/2),'underline must not cross a half-note beat in 2/2')
                    self.assertAlmostEqual(float(n.findtext('TextLine/lineWidth')),.11)
                elif n.tag in ['Chord','Rest']:break
        chord=root.findall('Score/Staff')[-1]
        for n in chord.findall('Measure/voice/StaffText'):
            if n.findtext('text') in ['x','X','0']:
                self.assertEqual(n.findtext('align'),'center,baseline')
                self.assertEqual(float(n.find('offset').get('y')),1)
        first=chord.findall('Measure')[4].find('voice');t=F(0);names=[]
        for n in first:
            if n.tag=='location':t+=F(n.findtext('fractions','0'))*4
            elif n.tag=='StaffText' and n.findtext('text') in ['C','C7']:names.append((t,n.findtext('text')))
            elif n.tag in ['Chord','Rest']:break
        self.assertEqual(names,[(0,'C'),(F(3),'C7')])
        for n in root.findall(".//StaffText[text='–']"):
            self.assertEqual(n.findtext('align'),'center,baseline')
            self.assertAlmostEqual(float(n.find('offset').get('y')),.741)

    def test_cut_time_and_playable_support_voices(self):
        from entertainer import edition,midi
        music=edition('Quintet')
        self.assertEqual(music['meter'],[2,2]);self.assertEqual(music['tempo'],144)
        self.assertEqual(music['beat_tempo'],72)
        for record in self.records:
            root=read_score(self.dest/record['file'])
            ts=root.find('.//TimeSig');self.assertEqual(ts.findtext('sigN'),'2');self.assertEqual(ts.findtext('sigD'),'2')
            self.assertEqual(root.findtext('.//Tempo/text/sym'),'metNoteHalfUp')
        for part in music['parts'][1:3]:
            pitches=[]
            for events in part['measures']:
                for e in events:
                    self.assertGreaterEqual(F(e['duration']),1)
                    pitches.extend(midi(p)for p in e['pitches'])
            self.assertTrue(all(abs(a-b)<=5 for a,b in zip(pitches,pitches[1:])))
            for bar in [7,11,15,19]:self.assertEqual(part['measures'][bar][-1]['pitches'],[])

    def test_complete_form_source_trace_and_final_cadence(self):
        from entertainer import edition, SOURCE, RAW, midi
        music=edition('Quintet')
        self.assertEqual(len(music['form']),152)
        starts=[(i+1,b['section'])for i,b in enumerate(music['form'])if b['pass_start']]
        self.assertEqual(starts,[(1,'Intro'),(5,'A'),(21,'A'),(37,'B'),(53,'B'),(69,'A'),(85,'C'),(101,'C'),(117,'Bridge'),(121,'D'),(137,'D')])
        self.assertEqual(music['form'][-1]['source_bar'],92)
        self.assertEqual(sum(F(x)for x in music['measure_beats'])*60/music['tempo'],F(760,3))
        original={n['id']:n for n in RAW}
        for bar in music['parts'][0]['measures']:
            for e in bar:
                if not e['pitches']:continue
                n=original[e['source_start']]
                self.assertIn(midi(e['pitches'][0])-n['pitch'],[-12,0])
        self.assertEqual(music['key_changes'],{0:0,84:-1,116:0})
        for record in self.records:
            root=read_score(self.dest/record['file'])
            self.assertEqual(root.find('Score/Staff').findall('Measure')[-1].findtext('voice/BarLine/subtype'),'end')
        bass=music['parts'][3]
        self.assertTrue(all(28<=midi(p)<=67 for es in bass['measures']for e in es for p in e['pitches']))
        self.assertTrue(all(not e['pitches']for es in bass['measures'][:3]for e in es))

    def test_quartet_preserves_complete_melody_and_uses_two_real_leads(self):
        from entertainer import edition, midi, RAW
        music=edition('Quartet');old=edition('Solo')['parts'][0]['measures']
        roles={p['role']:p['measures']for p in music['parts']}
        self.assertEqual(list(roles),['h1','h2','bass','chord'])
        trace=music['melodic_handoffs'];main=[t for t in trace if t['kind']=='melody']
        want=[(i+1,e['onset'],e['duration'],e['source_start'])for i,es in enumerate(old)for e in es if e['pitches']]
        self.assertEqual(sorted(want),sorted((e['bar'],e['onset'],e['duration'],e['source'])for e in main))
        for role in ['h1','h2']:
            self.assertGreater(sum(t['owner']==role for t in main),300)
            self.assertEqual(sum(t['owner']==role and t['kind']=='source_inner_line'for t in trace),20)
        self.assertEqual(next(e['pitches']for e in roles['h1'][7]if e['onset']=='3'),['D4'])
        self.assertTrue(any(e['pitches']==['E5']for e in roles['h2'][16]))
        self.assertTrue(any(e['pitches']==['E5']for e in roles['h1'][32]))
        for role in ['h1','h2']:
            self.assertTrue(all(48<=midi(p)<=98 for es in roles[role]for e in es for p in e['pitches']))
        self.assertGreater(sum(t['kind']=='counter_accompaniment'for t in trace),250)
        original_ids={n['id']for n in RAW}
        self.assertTrue(all(t['source']in original_ids for t in trace if t['kind']!='counter_accompaniment'))

    def test_current_delivery_contains_only_requested_three_forms(self):
        records=templates.build_templates(self.dest)
        self.assertEqual({r['form']for r in records},{'Solo_Piano','Duet','Quartet'})
        self.assertEqual(len(records),6)
        from entertainer import edition
        duet=edition('Duet');quartet=edition('Quartet')
        self.assertEqual(duet['parts'],quartet['parts'][:2])
        self.assertEqual(duet['melodic_handoffs'],quartet['melodic_handoffs'])

    def test_solo_piano_preserves_original_left_hand_and_complete_wind_line(self):
        from entertainer import edition,RAW,midi
        music=edition('Solo_Piano');old=edition('Solo')
        self.assertEqual(music['parts'][0],old['parts'][0])
        want=sorted((2*n['a'],2*n['b'],n['pitch'])for n in RAW if n['track']==2)
        actual=[]
        for part in music['parts'][1:]:
            for rows in [part['measures']]+part.get('additional_voices',[]):
                for mi,es in enumerate(rows):
                    for e in es:
                        if str(e['source_start']).startswith('original-lh:'):
                            a=4*mi+F(e['onset']);b=a+F(e['duration'])
                            actual.extend((a,b,midi(p))for p in e['pitches'])
        self.assertEqual(actual and sorted(actual),want)
        templates.build_templates(self.dest,forms=['Solo_Piano'])
        root=read_score(self.dest/'HarpScore_Solo_Piano_Numbered.mscz')
        staves=root.findall('Score/Staff')
        self.assertTrue(staves[0].findall('.//StaffText'))
        for s in staves[1:]:
            self.assertFalse(s.findall('.//StaffText'))
            self.assertTrue(any(n.findtext('color')is None for n in s.findall('.//Note')))
        self.assertTrue(any(len(m.findall('voice'))==2 for m in staves[1].findall('Measure')))
        with zipfile.ZipFile(self.dest/'HarpScore_Solo_Piano_Numbered.mscz')as z:
            style=E.fromstring(z.read('score_style.mss'))
        self.assertEqual(style.findtext('Style/showHeader'),'1')
        self.assertEqual(style.findtext('Style/headerFirstPage'),'0')
        for key in ['oddHeaderL','oddHeaderR','evenHeaderL','evenHeaderR']:
            self.assertEqual(style.findtext('Style/'+key),'')

    def test_chromatic_double_stops_match_reeds_and_preserve_existing_lines(self):
        from entertainer import quartet_rows,midi
        from chromatic import double_stop_options
        self.assertTrue(double_stop_options([60,64])) # C4/E4 blow 5+6
        self.assertTrue(double_stop_options([65,68])) # F4/Ab4 blow 6+7, slide in
        self.assertFalse(double_stop_options([67,71])) # G4/B4: opposite breath
        self.assertFalse(double_stop_options([66,69])) # F#4/A4: mixed slide
        before,_=quartet_rows(False);after,_=quartet_rows();count=0
        for role in before:
            for a,b in zip(before[role],after[role]):
                self.assertEqual(len(a),len(b))
                for old,new in zip(a,b):
                    for key in ['onset','duration','velocity','source_start','tie_in','tie_out']:
                        self.assertEqual(old[key],new[key])
                    self.assertEqual(old['pitches'],new['pitches'][:len(old['pitches'])])
                    if 'double_stop'in new:
                        count+=1
                        self.assertIn(new['double_stop']['fingering'],double_stop_options([midi(p)for p in new['pitches']]))
        self.assertGreaterEqual(count,20)
        templates.build_templates(self.dest,forms=['Quartet'])
        display=json.loads((self.dest/'events/Quartet_Numbered_display.json').read_text())
        for bar in display:
            if bar['part']not in ['h1','h2']:continue
            for token in bar['tokens']:
                self.assertEqual(sorted(p for p in token['pitches']),sorted(n['pitch']for n in token['notes']if n['pitch']))
                self.assertEqual(len({n['y']for n in token['notes']}),len(token['notes']))
                if len(token['notes'])==2:
                    self.assertEqual([n['size']for n in token['notes']],[9,9])
                    self.assertAlmostEqual(sum(n['y']for n in token['notes']),0)
        root=read_score(self.dest/'HarpScore_Quartet_Numbered.mscz')
        self.assertIsNone(root.find("Score/Part/Staff[@id='2']/distOffset"))
        with zipfile.ZipFile(self.dest/'HarpScore_Quartet_Numbered.mscz')as z:
            style=E.fromstring(z.read('score_style.mss'))
        original=E.parse(ROOT/'templates/layout/Quartet_Numbered.mss').getroot()
        for key in ['minSystemDistance','maxSystemDistance']:
            self.assertEqual(style.findtext('Style/'+key),original.findtext('Style/'+key))

    def test_quartet_pickups_belong_to_the_following_phrase(self):
        from entertainer import edition
        trace=[x for x in edition('Quartet')['melodic_handoffs']if x['kind']=='melody']
        # Source-specific phrase boundaries, not a general modulo-bar rule.
        pickups=[(4,3,5),(6,F(5,2),7),(8,3,9),(10,3,11),(12,3,13),(14,F(5,2),15),(16,3,17),(20,3,21),(22,F(5,2),23),(24,3,25),(26,3,27),(28,3,29),(30,F(5,2),31),(32,3,33),(36,F(5,2),37),(44,F(5,2),45),(52,F(5,2),53),(60,F(5,2),61),(68,3,69),(70,F(5,2),71),(72,3,73),(74,3,75),(76,3,77),(78,F(5,2),79),(80,3,81),(100,1,101)]
        for bar,at,arrival in pickups:
            incoming=next(x['owner']for x in trace if x['bar']==arrival and F(x['onset'])==0)
            owners={x['owner']for x in trace if x['bar']==bar and F(x['onset'])>=at}
            self.assertEqual(owners,{incoming},(bar,arrival))

    def test_quartet_labels_attach_to_sounding_attacks_and_hide_nc(self):
        records=templates.build_templates(self.dest,forms=['Quartet'])
        self.assertEqual(len(records),2)
        for record in records:
            r=read_score(self.dest/record['file']);self.assertEqual(len(r.findall('Score/Staff')),4)
            self.assertNotIn('N.C.',E.tostring(r).decode())
            chord=r.findall('Score/Staff')[-1]
            for m in chord.findall('Measure'):
                at=F(0);labels=[];attacks=[]
                for n in m.find('voice'):
                    if n.tag=='location':at+=F(n.findtext('fractions','0'))*4
                    elif n.tag=='Harmony':labels.append(at)
                    elif n.tag=='StaffText'and n.findtext('size')=='9':labels.append(at)
                    elif n.tag in ['Chord','Rest']:
                        if n.tag=='Chord'and n.find("Note/Spanner[@type='Tie']/prev")is None:attacks.append(at)
                        at+=DURATIONS[n.findtext('durationType')]*(2-F(1,2**int(n.findtext('dots','0'))))
                self.assertTrue(set(labels)<=set(attacks))

    def test_initial_eighth_rest_is_not_joined_to_three_eighth_notes(self):
        from entertainer_notation import numbered_annotations, pieces
        from entertainer import event
        events=[event(F(i,2),F(1,2),[]if i==0 else ['C5'],source=str(i))for i in range(4)]
        parts=[p for e in events for p in pieces(e)]
        annotations,_=numbered_annotations(parts,'h1')
        starts=[at for at,items in annotations.items()if any(x.tag=='Spanner'and x.find('TextLine')is not None for x in items)]
        self.assertEqual(starts,[F(1,2)])
        self.assertTrue(any(x.findtext('text')=='0'for x in annotations[F(0)]))

    def test_rebuild_is_reproducible(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            ra=templates.build_templates(a);rb=templates.build_templates(b)
            self.assertEqual([r['sha256'] for r in ra],[r['sha256'] for r in rb])

if __name__=='__main__':unittest.main()
