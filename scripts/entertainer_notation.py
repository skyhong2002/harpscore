"""Native MuseScore notation for the explicit public-domain Entertainer arrangement.

This supports this arrangement's monophonic lines/chord attacks and explicit durations;
it does not parse arbitrary scores or transcribe audio. The same event list feeds
both editions. All graphic overlays must be rebuilt after musical edits.
"""
from collections import defaultdict
from fractions import Fraction as F
from copy import deepcopy
import xml.etree.ElementTree as E
from entertainer import TITLE, HARMONIES, MEASURE_BEATS, SECTION_MARKS, KEY_CHANGES, midi, tpc
from pathlib import Path

VALUES={'whole':F(4),'half':F(2),'quarter':F(1),'eighth':F(1,2),'16th':F(1,4)}

def el(tag,value=None,**attrs):
    n=E.Element(tag,{k:str(v) for k,v in attrs.items()})
    if value is not None:
        # MuseScore's location reader treats a bare integer as ticks/1024,
        # not whole-note units. Keep /1 for integral forward/backward moves.
        if tag=='fractions':
            fraction=F(value)
            n.text=f'{fraction.numerator}/{fraction.denominator}'
        else:n.text=str(value)
    return n

def put(p,tag,value=None,**attrs):
    n=el(tag,value,**attrs);p.append(n);return n

def setv(p,tag,value):
    n=p.find(tag)
    if n is None:n=put(p,tag)
    n.text=str(value);return n

def loc(beats):
    n=el('location');put(n,'fractions',F(beats)/4);put(n,'timeTick',1);return n

def spelling(d):
    for kind,base in VALUES.items():
        for dots in [0,1]:
            if base*(F(3,2) if dots else 1)==d:return kind,dots
    raise ValueError(f'Unsupported study duration: {d}')

def pieces(event):
    t=F(event['onset']);remaining=F(event['duration']);result=[]
    while remaining:
        # Keep a visible beat boundary for syncopated short-note passages.
        limit=min(remaining,2-t%2) if t%2 else remaining
        choices=[(base*(F(3,2) if dot else 1),kind,dot) for kind,base in VALUES.items() for dot in [0,1]]
        length,kind,dots=max(x for x in choices if x[0]<=limit)
        result.append({**event,'t':t,'d':length,'kind':kind,'dots':dots})
        t+=length;remaining-=length
    return result

def prepare_parts(measures):
    rows=[[p for e in es for p in pieces(e)] for es in measures]
    flattened=[(mi,p)for mi,ps in enumerate(rows)for p in ps]
    for i,(mi,p)in enumerate(flattened):
        p['tie_in']=False;p['tie_out']=False
        for key,j in [('prev',i-1),('next',i+1)]:
            if 0<=j<len(flattened):
                mj,q=flattened[j]
                linked=bool(p['pitches'] and p['pitches']==q['pitches'] and p['source_start']==q['source_start'])
                if linked:
                    p['tie_in' if key=='prev' else 'tie_out']=True
                    p['tie_'+key+'_d']=q['d'];p[key+'_measures']=mj-mi
                    p[key+'_fractions']=(q['t']-p['t'])/4;p[key+'_t']=q['t']
    return rows

def txt(value,x=.6,y=0,size=12,baseline=False,bold=False):
    models=E.parse(Path(__file__).resolve().parents[1]/'templates/layout/numbered-glyphs.xml').getroot()
    model='weak' if value=='x' else 'strong' if value=='X' else 'dash' if value=='–' else 'durationDot' if value=='·' else 'octaveDot' if value=='•' else 'sharp' if value in ['♯','♮','♭'] else 'digit'
    n=deepcopy(next(x for x in models if x.get('model')==model));n.attrib.pop('model',None)
    setv(n,'size',size);setv(n,'bold',int(bold));setv(n,'text',value)
    setv(n,'align','center,baseline' if baseline else 'center,center')
    n.find('offset').attrib.update(x=str(x),y=str(y))
    return n

def dynamic(value,jianpu,chord=False):
    n=el('Dynamic');put(n,'subtype',value);put(n,'velocity',0);put(n,'direction','down')
    if jianpu:put(n,'autoplace',0);put(n,'offset',x=0,y=6.2 if chord else 4.35)
    return n

def line(d,y):
    start=el('Spanner',type='TextLine');tl=put(start,'TextLine')
    put(tl,'lineWidth',.11);put(tl,'lineStyle','solid');put(tl,'placement','above')
    put(tl,'offset',x=.6,y=y);put(tl,'autoplace',0)
    seg=put(tl,'Segment');put(seg,'subtype',0);put(seg,'offset',x=.6,y=y)
    put(seg,'off2',x=2.36,y=0);put(seg,'autoplace',0)
    put(put(put(start,'next'),'location'),'fractions',d/4)
    end=el('Spanner',type='TextLine');put(put(put(end,'prev'),'location'),'fractions',-d/4)
    return start,end

def tie(note,piece,jianpu,visible=True):
    if piece['tie_out']:
        sp=put(note,'Spanner',type='Tie');t=put(sp,'Tie')
        if jianpu:
            put(t,'visible',int(visible));put(t,'up','up');put(t,'color',r=0,g=0,b=0,a=255 if visible else 0)
            seg=put(t,'TieSegment',no=0)
            put(seg,'o1',x=0,y=-1.6);put(seg,'o4',x=0,y=-1.6);put(seg,'autoplace',0)
        target=put(put(sp,'next'),'location');put(target,'measures',piece['next_measures']);put(target,'fractions',piece['next_fractions'])
    if piece['tie_in']:
        sp=put(note,'Spanner',type='Tie')
        target=put(put(sp,'prev'),'location');put(target,'measures',piece['prev_measures']);put(target,'fractions',piece['prev_fractions'])

def native(piece,jianpu,chord=False):
    pitches=piece['pitches'];n=el('Chord' if pitches else 'Rest')
    if piece['dots']:put(n,'dots',piece['dots'])
    put(n,'durationType',piece['kind'])
    if piece.get('articulation')=='staccato' and not piece['tie_in']:
        art=put(n,'Articulation');put(art,'subtype','articStaccatoAbove')
        put(art,'direction','up')
    if piece['d']<1:
        # Always begin a new beam at half-note beats, including Chord.
        put(n,'BeamMode','begin' if piece['t']%2==0 else 'auto')
    if jianpu:
        put(n,'visible',1);put(n,'small',1)
        if pitches:put(n,'noStem',1);put(n,'BeamMode','no')
        else:
            put(n,'color',r=255,g=255,b=255,a=0)
            for _ in range(piece['dots']):put(put(n,'NoteDot'),'visible',0)
    for i,pitch in enumerate(pitches):
        note=put(n,'Note');put(note,'pitch',midi(pitch));put(note,'tpc',tpc(pitch))
        put(note,'veloType','user');put(note,'velocity',piece['velocity'])
        if jianpu or chord:
            put(note,'fixed',1);put(note,'fixedLine',0);put(note,'visible',int(i==0))
            if len(pitch)==3:
                acc=put(note,'Accidental');put(acc,'subtype','sharp' if '#' in pitch else 'flat');put(acc,'visible',0)
        if jianpu:
            put(note,'color',r=255,g=255,b=255,a=0)
            for _ in range(piece['dots']):put(put(note,'NoteDot'),'visible',0)
        # Tied continuations represented as extension dashes have no visible arc.
        target_is_dash=(piece.get('tie_out') and piece['next_t']!=0 and piece['next_t'].denominator==1
                        and piece['tie_next_d']>=1)
        tie(note,piece,jianpu,visible=i==0 and not target_is_dash and not (piece['tie_in'] and piece['t']!=0 and piece['t'].denominator==1 and piece['d']>=1))
    return n

# Avenir Next Regular 12pt and Arial bullet 5pt, 1.5mm spatium.
# Normal MuseScore SVG aligns StaffText ink-left despite center alignment;
# compensate half the two ink widths, not a piece-specific note position.
OCTAVE_DOT_X={'1':.198756,'2':.493678,'3':.492267,'4':.557178,'5':.485211,'6':.503556,'7':.447111}

def numbered_annotations(parts,role):
    annotations=defaultdict(list);display=[];accidentals={};chord=role=='chord'
    for piece in parts:
        t,d=piece['t'],piece['d'];pitches=piece['pitches'];level={'eighth':1,'16th':2}.get(piece['kind'],0)
        # Simultaneous wind pitches are stacked, low pitch on the normal
        # baseline. Every pitch receives its own accidental and octave dots.
        # Chord harp remains a rhythm sign, not a stack of its playback reeds.
        voices=sorted(pitches,key=midi)if pitches and not chord else [None]
        stacked=len(voices)>1;scale=.75 if stacked else 1
        tokens=[]
        for vi,p in enumerate(voices):
            # Both reduced digits straddle the ordinary numeral centre.
            # Neither keeps the single-note centre as its own baseline.
            y=1.15-2.3*vi if stacked else 0;glyph='0';octv=0
            if pitches:
                if chord:glyph='X' if piece['velocity']>=56 else 'x'
                else:
                    step=p[0];alter=1 if '#' in p else -1 if 'b' in p else 0
                    glyph=str('CDEFGAB'.index(step)+1)
                    octv=int(p[-1])-(3 if role=='bass' else 5)
                    if piece['tie_in'] and t!=0 and t.denominator==1 and d>=1:glyph='–';octv=0
                    else:
                        key=(step,int(p[-1]));old=accidentals.get(key,0)
                        if alter!=old:
                            annotations[t].append(txt('♯' if alter>0 else '♭' if alter<0 else '♮',x=-.05,y=y-1.25*scale,size=7*scale))
                        accidentals[key]=alter
            annotations[t].append(txt(glyph,y=y+(.741*scale if glyph=='–' else 1 if chord else 0),
                                      size=(13 if glyph=='–' else 12)*scale,baseline=chord or glyph=='–'))
            tokens.append({'pitch':p,'glyph':glyph,'octave':octv,'y':y,'size':12*scale})
            for j in range(abs(octv)):
                annotations[t].append(txt('•',x=.6+OCTAVE_DOT_X[glyph]*scale,y=y+((-1.3-j*.48) if octv>0 else 1.6+level*.4+j*.48)*scale,size=5*scale))
            if d>=2:
                for j in range(1,int(d)):
                    annotations[t+j].append(txt('–' if pitches else '0',y=y+(.741*scale if pitches else 1 if chord else 0),
                                               size=(13 if pitches else 12)*scale,baseline=bool(pitches) or chord))
            elif piece['dots']:
                annotations[t+VALUES[piece['kind']]].append(txt('·',y=y+.4*scale,size=11.5*scale,bold=True))
        display.append({'onset':str(t),'glyph':tokens[0]['glyph'],'level':level,'duration':str(d),
                        'octave':tokens[0]['octave'],'pitches':pitches,'velocity':piece['velocity'],
                        'notes':tokens})
    # Independent underline runs within each half-note beat. A singleton still
    # gets a real TextLine, rather than a font underscore of unrelated metrics.
    for beat in range(0,4,2):
        group=[p for p in parts if beat<=p['t']<beat+2]
        # A leading eighth rest in 0 + three eighth notes is not beamed
        # to the following notes. Leave its 0 separate; start at the sound.
        if (len(group)==4 and not group[0]['pitches']
                and all(p['kind']=='eighth'and p['d']==F(1,2)for p in group)):
            group=group[1:]
        for level in [1,2]:
            runs=[];run=[]
            for p in group:
                if {'eighth':1,'16th':2}.get(p['kind'],0)>=level:run.append(p)
                elif run:runs.append(run);run=[]
            if run:runs.append(run)
            for run in runs:
                a=run[0]['t'];b=run[-1]['t'] if len(run)>1 else a+F(1,480)
                stacked_run=not chord and any(len(p['pitches'])>1 for p in run)
                start,end=line(b-a,(2.35 if stacked_run else 1.32)+(level-1)*.4)
                annotations[a].append(start);annotations[b].append(end)
    return annotations,display

def harmony(name):
    # Same native Harmony structure used in Summer; MuseScore can avoid
    # collisions between chord symbols and the native dynamics.
    h=el('Harmony');put(h,'play',0);info=put(h,'harmonyInfo')
    if name=='N.C.':put(info,'name','N.C.')
    else:
        import re
        root,suffix=re.fullmatch(r'([A-G][#b]?)(.*)',name).groups()
        if suffix:put(info,'name',suffix)
        put(info,'root',tpc(root+'4'))
    put(h,'placement','below')
    return h

def fill_score(root,data,jianpu):
    score=root.find('Score');graphics=[]
    for key in ['showInvisible','showUnprintable','showFrames']:setv(score,key,0)
    for si,(staff,part)in enumerate(zip(score.findall('Staff'),data['parts'])):
        role=part['role'];chord=role=='chord';current_dynamic=None;prepared=prepare_parts(part['measures'])
        part_numbered=jianpu and not role.startswith('piano')
        extra=[prepare_parts(rows)for rows in part.get('additional_voices',[])]
        header=staff.find('Measure/voice');headers=[deepcopy(n)for n in header if n.tag in ['Clef','KeySig','TimeSig','Tempo']]
        for old in list(staff.findall('Measure')):staff.remove(old)
        for mi,(events,all_parts,length)in enumerate(zip(part['measures'],prepared,MEASURE_BEATS)):
            measure=put(staff,'Measure');v=put(measure,'voice')
            if mi==0:
                for n in deepcopy(headers):
                    if n.tag=='KeySig':setv(n,'concertKey',0)
                    if n.tag=='TimeSig':setv(n,'sigN',2);setv(n,'sigD',2)
                    if n.tag=='Tempo':
                        setv(n,'tempo',2.4);setv(n,'followText',0);tx=n.find('text');tx.clear();put(tx,'sym','metNoteHalfUp').tail=' = 72'
                        if part_numbered:
                            setv(n,'autoplace',0)
                            offset=n.find('offset')
                            if offset is None:offset=put(n,'offset')
                            offset.attrib.update(x='0',y='-2.4')
                    v.append(n)
            if mi in KEY_CHANGES and mi!=0:
                key=put(v,'KeySig');put(key,'concertKey',KEY_CHANGES[mi])
                if part_numbered:put(key,'visible',0)
            ann=defaultdict(list)
            if part_numbered:
                a,display=numbered_annotations(all_parts,role)
                for t,items in a.items():ann[t].extend(items)
                graphics.append({'part':role,'measure':mi,'tokens':display})
                if mi==0 and si==0:ann[F(0)].append(txt('2/2',x=-3.4,y=-2.7,size=9))
            if si==0 and mi in SECTION_MARKS:
                mark=el('RehearsalMark');put(mark,'text',SECTION_MARKS[mi]);put(mark,'autoplace',0);put(mark,'offset',x=0,y=-4.5);ann[F(0)].append(mark)
            if data.get('chord_label_policy')=='first_sounding_attack':
                for e in events:
                    if not e['pitches']:continue
                    value='mf'if role in ['h1','h2']and e['velocity']>=70 else 'mp'
                    if value!=current_dynamic:
                        ann[F(e['onset'])].append(dynamic(value,part_numbered,chord));current_dynamic=value
            elif mi==0 or mi in SECTION_MARKS:
                ann[F(0)].append(dynamic(('f'if mi==0 else 'mf')if role=='h1'else 'mp',part_numbered,chord))
            if role in ['chord','piano']:
                changes=HARMONIES[mi]
                for ci,(beat,name)in enumerate(changes):
                    at=F(beat)
                    if data.get('chord_label_policy')=='first_sounding_attack':
                        if name=='N.C.':continue
                        end=F(changes[ci+1][0])if ci+1<len(changes)else length
                        attacks=[F(e['onset'])for e in events if e['pitches']and not e['tie_in']and at<=F(e['onset'])<end]
                        if not attacks:continue
                        at=min(attacks)
                    ann[at].append(txt(name.replace('dim7','°7').replace('#','♯').replace('b','♭'),y=4.4,size=9,baseline=True)if part_numbered else harmony(name))
            last=F(0)
            for t,items in sorted(ann.items()):
                if t!=last:v.append(loc(t-last))
                v.extend(items);last=t
            if last:v.append(loc(-last))
            for p in all_parts:
                n=native(p,part_numbered,chord)
                if extra:
                    if n.tag=='Chord':put(n,'StemDirection','up')
                    elif all(not e['pitches']for e in events):put(n,'visible',0)
                v.append(n)
                if part_numbered:put(put(v,'Segment'),'leadingSpace',.75 if p['t'].denominator==1 else .4)
            for rows in extra:
                ps=rows[mi]
                if not any(p['pitches']for p in ps):continue
                second=put(measure,'voice')
                for p in ps:
                    n=native(p,False)
                    if n.tag=='Chord':put(n,'StemDirection','down')
                    second.append(n)
            if mi==len(MEASURE_BEATS)-1:put(put(v,'BarLine'),'subtype','end')
    return graphics
