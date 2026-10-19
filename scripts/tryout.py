"""Generate an original four-bar exercise for an agent's MuseScore/Jianpu trial.

No external packages, GUI automation, PDF export or audio transcription.
"""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import re
import xml.etree.ElementTree as E

MELODY = [
    [('D5','3/2',68),('F#5','1/4',64),('G5','1/4',64),('A5','1/2',66),('B5','1/2',66),('A5','1',66)],
    [('F#5','1/2',64),('F#5','1/2',64),('F5','1',64),('F#5','1',64),('F#6','1',64)],
    [(None,'1/2',0),('E5','1',64),('F#5','1',64),('G5','1/2',64),('A5','1',64)],
    [('C#5','3',60),(None,'1/2',0),('D5','1/2',64)],
]
CHORDS = {'C':['C4','E4','G4'],'G':['G3','B3','D4'],'F':['F3','A3','C4']}
HARMONIES = [['C','G'],['C'],['F'],['C']]

def event_rows():
    parts=[]
    for name,measures in [('Chromatic H.',MELODY),('Chord',None)]:
        bars=[]
        for mi in range(4):
            if measures is None:
                root=HARMONIES[mi][0]
                seq=[(None,'1/2',0),(root,'1/2',48)]*4
                if mi==0:seq=seq[:4]+[(None,'1/2',0),('G','1/2',64),(None,'1/2',0),('G','1/2',48)]
                if mi==3:seq=[(root,'4',64)]
            else:seq=measures[mi]
            t=F(0);bar=[]
            for pitch,duration,velocity in seq:
                bar.append({'onset':str(t),'duration':duration,'pitches':CHORDS[pitch] if measures is None and pitch else ([pitch] if pitch else []),'velocity':velocity})
                t+=F(duration)
            if t!=4:raise ValueError(f'{name} measure {mi+1} has {t} beats')
            bars.append(bar)
        parts.append({'name':name,'measures':bars})
    return parts

def node(parent,tag,text=None,**attrs):
    child=E.SubElement(parent,tag,attrs)
    if text is not None:child.text=str(text)
    return child

def pitch_node(n,pitch):
    step,alt,octave=re.fullmatch(r'([A-G])([#b]?)(\d)',pitch).groups()
    p=node(n,'pitch');node(p,'step',step)
    if alt:node(p,'alter',1 if alt=='#' else -1)
    node(p,'octave',octave)

TYPES={F(4):('whole',False),F(3):('half',True),F(2):('half',False),F('3/2'):('quarter',True),F(1):('quarter',False),F('1/2'):('eighth',False),F('1/4'):('16th',False)}

def write_fixture(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    parts=event_rows()
    root=E.Element('score-partwise',version='4.0')
    work=node(root,'work');node(work,'work-title','HarpScore original trial')
    ident=node(root,'identification');node(ident,'creator','HarpScore contributors',type='composer')
    plist=node(root,'part-list')
    for pi,part in enumerate(parts,1):
        sp=node(plist,'score-part',id=f'P{pi}');node(sp,'part-name',part['name'])
    for pi,part in enumerate(parts,1):
        p=node(root,'part',id=f'P{pi}')
        for mi,events in enumerate(part['measures'],1):
            measure=node(p,'measure',number=str(mi))
            if mi==1:
                attr=node(measure,'attributes');node(attr,'divisions',4)
                key=node(attr,'key');node(key,'fifths',2)
                time=node(attr,'time');node(time,'beats',4);node(time,'beat-type',4)
                clef=node(attr,'clef');node(clef,'sign','G');node(clef,'line',2)
                direction=node(measure,'direction',placement='above');dt=node(direction,'direction-type')
                metro=node(dt,'metronome');node(metro,'beat-unit','quarter');node(metro,'per-minute',120)
                node(direction,'sound',tempo='120')
            for event in events:
                onset=F(event['onset']);duration=F(event['duration'])
                if pi==2 and (onset==0 or (mi==1 and onset==2)):
                    h=node(measure,'harmony');hn='G' if mi==1 and onset==2 else HARMONIES[mi-1][0]
                    hr=node(h,'root');node(hr,'root-step',hn);node(h,'kind','major')
                # The syncopation crosses beat three. Spell it as tied eighths.
                segments=[F('1/2'),F('1/2')] if pi==1 and mi==3 and onset==F('3/2') else [duration]
                for si,d in enumerate(segments):
                    for ni,pitch in enumerate(event['pitches'] or [None]):
                        n=node(measure,'note')
                        if ni:node(n,'chord')
                        if pitch:pitch_node(n,pitch)
                        else:node(n,'rest')
                        node(n,'duration',int(d*4))
                        if len(segments)>1:node(n,'tie',type='start' if si==0 else 'stop')
                        typ,dot=TYPES[d];node(n,'type',typ)
                        if dot:node(n,'dot')
                        if len(segments)>1:
                            nt=node(n,'notations');node(nt,'tied',type='start' if si==0 else 'stop')
                    # Raw velocity reference remains authoritative in events.json.
                    # The agent must map it explicitly when building its playback layer.
            if mi==4:
                bar=node(measure,'barline',location='right');node(bar,'bar-style','light-heavy')
    E.indent(root)
    E.ElementTree(root).write(destination/'original.musicxml',encoding='utf-8',xml_declaration=True)
    payload={'format':'harpscore-events-0.1','tempo':120,'meter':[4,4],'parts':parts}
    (destination/'events.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    expected={'bar_count':4,'beats_per_bar':4,'total_quarter_beats_per_part':16,
        'chromatic_unpointed_one':'C5','first_numeral':'2','first_duration_dot_onset':'1',
        'second_measure_accidental_sequence':['#4','4','natural4','#4','#4 in next octave'],
        'third_measure_continuous_tied_pitch':'F#5','chord_change_m1_onset':'2',
        'chord_next_attack_after_change':'5/2','velocity_source':'events.json',
        'must_verify_visually':['quarter-beat underline gaps','x/X/0 baseline','dash optical centre','dynamics and harmony clearance'],
        'musescore_import_render_playback':'not verified by this script'}
    (destination/'expected.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n')
    return payload

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args();write_fixture(args.out)
    print(f'Original trial fixture created in {args.out}; open original.musicxml in MuseScore. Rendering/playback not yet verified.')
