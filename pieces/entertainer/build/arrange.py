"""Source-traceable full Entertainer arrangement in performance order.

The public-domain MIDI encodes the original piano with repeats unfolded. This
bounded arrangement keeps its complete melody/form and explicitly curates wind
support, bass and Chord roles. It is not a general-purpose transcription engine.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from copy import deepcopy
import json,re,sys
PIECE=Path(__file__).resolve().parents[1]
ROOT=PIECE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
SOURCE=json.loads((PIECE/'source/source-events.json').read_text())
PLAN=json.loads((PIECE/'source/arrangement-plan.json').read_text())
TITLE='The Entertainer';METER=(2,2)
SOURCE_MEASURE_BEATS=[F(x)for x in SOURCE['measure_beats']]
MEASURE_BEATS=[2*x for x in SOURCE_MEASURE_BEATS]
SOURCE_HARMONIES=[PLAN['harmonies'][str(b['source_bar'])]for b in SOURCE['form']]
HARMONIES=[[(str(2*F(a)),name)for a,name in bar]for bar in SOURCE_HARMONIES]
SECTION_MARKS={4:'A',36:'B',68:'A',84:'C',120:'D'}
KEY_CHANGES={0:0,84:-1,116:0}
NATURAL={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
TPC={'C':14,'D':16,'E':18,'F':13,'G':15,'A':17,'B':19}

def midi(p):
 step,alt,octv=re.fullmatch(r'([A-G])([#b]?)(\d)',p).groups()
 return (int(octv)+1)*12+NATURAL[step]+(1 if alt=='#'else -1 if alt else 0)
def tpc(p):
 step,alt,_=re.fullmatch(r'([A-G])([#b]?)(\d)',p).groups()
 return TPC[step]+(7 if alt=='#'else -7 if alt else 0)
def pitch(n,mi=0):
 key=SOURCE['form'][mi]['section']
 names=['C','C#','D','D#','E','F','F#','G','G#','A','Bb','B']
 # Retain the source's chromatic approaches. Flat-key passing notes and
 # diminished-seventh spellings in accompaniment are supplied by chord_tones.
 if mi==2 and n%12==8:names[8]='Ab'
 return names[n%12]+str(n//12-1)
def shifted(p,octaves):return p[:-1]+str(int(p[-1])+octaves)
def chord_tones(name):
 if name=='N.C.':return []
 root,quality=re.fullmatch(r'([A-G][#b]?)(.*)',name).groups()
 intervals={'':[0,4,7],'m':[0,3,7],'7':[0,4,7,10],'dim7':[0,3,6,9]}[quality]
 base=midi(root+'3');letters='CDEFGAB';start=letters.index(root[0]);result=[]
 for j,interval in enumerate(intervals):
  letter=letters[(start+2*j)%7];target=base+interval
  for octv in range(2,6):
   natural=12*(octv+1)+NATURAL[letter];alt=target-natural
   if alt in [-1,0,1]:result.append(letter+('b'if alt==-1 else '#'if alt==1 else '')+str(octv));break
  else:raise ValueError((name,interval))
 return result
CHORDS={n:chord_tones(n)for bar in SOURCE_HARMONIES for _,n in bar}
RAW=[{**n,'a':F(n['start']),'b':F(n['end'])}for n in SOURCE['notes']]
GROUPS={}
for track in [1,2]:
 groups=defaultdict(list)
 for n in RAW:
  if n['track']==track:groups[n['a']].append(n)
 GROUPS[track]=[(a,sorted(ns,key=lambda n:n['pitch']))for a,ns in sorted(groups.items())]

def event(t,d,pitches,velocity=58,source=None,**kw):
 return {'onset':str(t),'duration':str(d),'pitches':pitches,'velocity':velocity if pitches else 0,'source_start':source,'tie_in':False,'tie_out':False,**kw}

def fill_bar(attacks,mi,velocity=58):
 """Explicit attacks occupy their requested durations; fill genuine rests."""
 result=[];cursor=F(0)
 for a,b,ps,ident in sorted(attacks):
  assert a>=cursor,(mi,a,cursor)
  if a>cursor:result.append(event(cursor,a-cursor,[],source=None))
  if b>a:result.append(event(a,b-a,ps,velocity,ident));cursor=b
 if cursor<2:result.append(event(cursor,2-cursor,[],source=None))
 assert cursor<=2,(mi,cursor)
 return result

def melody_rows():
 rows=[]
 for mi in range(len(MEASURE_BEATS)):
  base=F(2*mi);end=base+2
  notes=[n for n in RAW if n['a']<end and n['b']>base and (n['track']==1 or mi in [2,3])]
  cuts=sorted({base,end}|{max(base,n['a'])for n in notes}|{min(end,n['b'])for n in notes})
  seq=[]
  for a,b in zip(cuts,cuts[1:]):
   active=[n for n in notes if n['a']<=a<n['b']]
   chosen=None
   if active:
    upper=[n for n in active if n['track']==1]
    top=max(upper or active,key=lambda n:n['pitch'])
    # Fold a same-onset piano octave doubling once, keeping its melodic note.
    # A lower piano voice moving under a held top note cannot steal the melody.
    lower=next((n for n in active if n['a']==top['a'] and n['pitch']==top['pitch']-12),None)
    section=SOURCE['form'][mi]['section'];local=SOURCE['form'][mi]['section_bar']
    chosen=lower if lower is not None and section not in ['B','C','Intro']else top
    if mi==3 and lower is not None and top['track']==1:chosen=lower
    if section=='D' and SOURCE['form'][mi]['section_bar']in [7,8]:chosen=top
   ident=chosen['id']if chosen else None
   if seq and seq[-1][3]==ident:seq[-1]=(seq[-1][0],b,chosen,ident)
   else:seq.append((a,b,chosen,ident))
  row=[]
  for a,b,n,ident in seq:
   value=n['pitch']if n else None
   section=SOURCE['form'][mi]['section'];local=SOURCE['form'][mi]['section_bar']
   if n and (section=='C' or (section=='B' and mi<52)):value-=12
   if n and section=='D' and local in [7,8] and value>67:value-=12
   row.append(event(a-base,b-a,[pitch(value,mi)]if n else [],76,ident,
                    tie_in=bool(n and a>n['a']),tie_out=bool(n and b<n['b']),source_pitch=n['pitch']if n else None))
  rows.append(row)
 return rows

GUIDES={'C':('G4','E4'),'C7':('G4','E4'),'F':('A4','F4'),'Fm':('Ab4','F4'),
        'G':('B4','D4'),'G7':('B4','F4'),'D7':('A4','C4'),'Bb':('F4','D4'),
        'Dm':('A4','F4'),'Gm':('Bb4','D4'),'E7':('G#4','D4'),'Am':('A4','C4'),
        'Db7':('Ab4','F4'),'F#dim7':('A4','Eb4')}

def support_rows(role):
 rows=[];which=0 if role=='h2'else 1
 for mi,bar in enumerate(SOURCE['form']):
  local=bar['section_bar'];section=bar['section']
  if section=='Intro':
   attacks=[]if mi<3 else [(F(1),F(2),['G4'if which==0 else 'B3'],f'{role}:intro')]
   rows.append(fill_bar(attacks,mi));continue
  if section=='A':
   # Preserve the deliberately revoiced theme. Source transitions are kept in H1/Bass.
   row=deepcopy(PLAN['first_theme_'+role][local-1])
   for e in row:e['source_start']=f'{role}:{mi}:{e["onset"]}'
   rows.append(row);continue
  changes=SOURCE_HARMONIES[mi];attacks=[]
  for j,(onset,name)in enumerate(changes):
   a=F(onset);b=F(changes[j+1][0])if j+1<len(changes)else F(2)
   tone=GUIDES[name][which]
   if attacks and attacks[-1][2]==[tone]:attacks[-1]=(attacks[-1][0],b,[tone],attacks[-1][3])
   else:attacks.append((a,b,[tone],f'{role}:{mi}:{a}'))
  if local%4==0 and attacks and attacks[-1][0]<F(3,2):
   a,b,ps,ident=attacks[-1];attacks[-1]=(a,F(3,2),ps,ident)
  rows.append(fill_bar(attacks,mi))
 return rows

def bass_rows():
 rows=[]
 for mi in range(len(MEASURE_BEATS)):
  base=F(2*mi);groups=[(a-base,ns)for a,ns in GROUPS[2]if base<=a<base+2]
  attacks=[]
  if mi<3:
   # The cascading unison introduction is carried intact by H1. Do not
   # invent sustained D/A bass notes underneath its chromatic line.
   attacks=[]
  else:
   for a,ns in groups:
    pcs={n['pitch']%12 for n in ns}
    if len(pcs)==1 or a.denominator==1:
     n=ns[0]['pitch']
     while n<28:n+=12
     while n>55:n-=12
     attacks.append((a,n))
  if not attacks:rows.append(fill_bar([],mi));continue
  has_sound_at_end=any(n['a']<base+2 and n['b']>base+F(3,2)for n in RAW if n['track']==2)
  ending=F(2)if has_sound_at_end else F(3,2)
  cells=[]
  for j,(a,n)in enumerate(attacks):
   b=attacks[j+1][0]if j+1<len(attacks)else max(a,ending)
   if a>=ending:continue
   # Retain chromatic spelling for source E-flat/A-flat/B-flat bass approaches.
   ps=pitch(n,mi)
   if n%12 in [3,8]:ps=('Eb'if n%12==3 else 'Ab')+str(n//12-1)
   cells.append((a,min(b,ending),[ps],f'bass:{mi}:{a}'))
  rows.append(fill_bar(cells,mi,60))
 return rows

def chord_rows():
 rows=[]
 for mi in range(len(MEASURE_BEATS)):
  base=F(2*mi);attacks=[]
  groups=[(a-base,ns)for a,ns in GROUPS[2]if base<=a<base+2]
  if mi<3:groups=[]
  for a,ns in groups:
   if len({n['pitch']%12 for n in ns})<2:continue
   name=next(n for onset,n in reversed(SOURCE_HARMONIES[mi])if F(onset)<=a)
   if name=='N.C.':continue
   duration=min(n['b']for n in ns)-base-a
   attacks.append((a,min(a+duration,F(2)),CHORDS[name][:],f'chord:{mi}:{a}'))
  # Piano polyphony may keep a chord tone under a new bass attack. Chord harp
  # reattacks only at the explicit chord attacks and never overlaps itself.
  for i in range(len(attacks)-1):
   a,b,ps,ident=attacks[i];attacks[i]=(a,min(b,attacks[i+1][0]),ps,ident)
  row=fill_bar(attacks,mi)
  for e in row:
   if e['pitches']:e['velocity']=48 if F(e['onset'])<1 else 64
  rows.append(row)
 return rows

CACHE={}
def rows_for(role):
 if not CACHE:
  CACHE.update(h1=melody_rows(),h2=support_rows('h2'),h3=support_rows('h3'),bass=bass_rows(),chord=chord_rows())
  CACHE['piano']=deepcopy(CACHE['chord']);CACHE['piano-lh']=deepcopy(CACHE['bass'])
  for es in CACHE['piano']:
   for e in es:e['pitches']=[shifted(p,1)for p in e['pitches']];e['velocity']=50 if e['pitches']else 0
  for es in CACHE['piano-lh']:
   for e in es:e['velocity']=54 if e['pitches']else 0
 return deepcopy(CACHE[role])

def edition(form):
 quartet,trace=quartet_rows()if form in ['Quartet','Duet']else (None,None)
 solo=solo_piano_parts()if form=='Solo_Piano'else None
 roles={'Solo':['h1'],'Solo_Piano':['h1','piano','piano-lh'],'Duet':['h1','h2'],'Duet_Piano':['h1','h2','piano','piano-lh'],'Quintet':['h1','h2','h3','bass','chord'],'Quartet':['h1','h2','bass','chord']}[form]
 parts=solo if solo else [{'role':r,'measures':deepcopy(quartet[r])if quartet is not None and r in quartet else rows_for(r)}for r in roles]
 for part in parts:
  for voice in [part['measures']]+part.get('additional_voices',[]):
   for es in voice:
    for e in es:
     for key in ['onset','duration']:e[key]=str(2*F(e[key]))
 return {'title':TITLE,'composer':'Scott Joplin','arranger':'skyhong.tw','license':'Public Domain composition; MIT HarpScore adaptation','tempo':144,'beat_unit':'half','beat_tempo':72,'meter':list(METER),'measure_beats':[str(x)for x in MEASURE_BEATS],'scope':SOURCE['scope'],'form':SOURCE['form'],'section_marks':SECTION_MARKS,'key_changes':KEY_CHANGES,'adaptations':PLAN['adaptations']+(['Two melodic winds preserve phrase pickups, moving support and source C-theme inner lines.']if quartet else [])+(['Piano retains every original LH pitch/onset/duration, distributed between the grand-staff hands; a separate upper voice carries arranged counterlines and source C-theme inner notes. Piano accompaniment velocities are reduced to balance the solo wind.']if solo else []),'melodic_handoffs':trace,'chord_label_policy':'first_sounding_attack'if quartet or solo else 'harmonic_time','parts':parts}


def solo_piano_parts():
 """Full wind line plus playable grand-staff ragtime accompaniment.

 Retain all original LH notes; move offbeat chord groups to the right hand.
 The independent moving line occupies a separate RH voice, so sustained
 counter-notes are not retriggered by each chord attack.
 """
 winds,trace=quartet_rows(False);melody_sources={t['source']for t in trace if t['kind']=='melody'}
 counter=[];hands={'piano':[],'piano-lh':[]}
 for mi,bar in enumerate(SOURCE['form']):
  cells=[]
  for role in winds:
   for e in winds[role][mi]:
    if not e['pitches']or e['source_start']in melody_sources:continue
    ps=e['pitches'][:]
    if bar['section']=='B'and mi<52:ps=[shifted(p,1)if midi(p)<60 else p for p in ps]
    cells.append((F(e['onset']),F(e['onset'])+F(e['duration']),ps,e['source_start']))
  counter.append(fill_bar(cells,mi,52))
  attacks={'piano':[],'piano-lh':[]};base=F(2*mi)
  for a,ns in GROUPS[2]:
   if not base<=a<base+2:continue
   role='piano'if len({n['pitch']%12 for n in ns})>1 else 'piano-lh'
   b=ns[0]['b'];assert all(n['b']==b for n in ns)
   assert b<=base+2
   attacks[role].append((a-base,b-base,[pitch(n['pitch'],mi)for n in ns],f'original-lh:{a}'))
  for role in hands:
   hands[role].append(fill_bar(attacks[role],mi,50 if role=='piano'else 56))
 return [{'role':'h1','measures':melody_rows()},
         {'role':'piano','measures':counter,'additional_voices':[hands['piano']]},
         {'role':'piano-lh','measures':hands['piano-lh']}]



def quartet_melody_owner(mi,t):
 """Ownership follows source melodic cells, including their anacruses.

 t is in original 2/4 quarter units. The A answers start at the actual
 C-D-D# / A-G pickups, and the next call starts at D-D#. They do not
 start at an arbitrary half bar. B/D exchanges preserve eight-bar periods.
 """
 bar=SOURCE['form'][mi];section=bar['section'];local=bar['section_bar'];t=F(t)
 if section=='Intro':
  if mi<3:return 'h1'if mi%2==0 else 'h2'
  return 'h2'if F(1)<=t<F(3,2)else 'h1'
 if section=='A':
  call='h2'if 20<=mi<36 else 'h1';answer='h1'if call=='h2'else 'h2'
  if local in [1,5,9]:return call
  if local in [2,10]:return call if t<F(5,4)else answer
  if local==6:return call if t<F(3,2)else answer
  if local in [3,7,11]:return answer
  if local in [4,8]:return answer if t<F(3,2)else call
  return answer
 if section=='B':
  # The first ending launches the high repeat; its E-F-F# belongs
  # to the incoming H1, not to the wind finishing the low C cadence.
  if mi==51 and t>=F(5,4):return 'h1'
  if mi==67 and t>=F(3,2):return 'h1'
  return 'h1'if local<8 or(local==8 and t<F(5,4))else 'h2'
 if section=='C':
  # The first ending's B-C-D-E-F-G is the pickup into the next A-G#-A.
  if mi==99 and t>=F(1,2):return 'h1'
  return 'h2'if mi<100 else 'h1'
 if section=='Bridge':return 'h2'
 first='h1'if mi<136 else 'h2'
 return first if local<=8 else ('h2'if first=='h1'else 'h1')


def quartet_rows(with_double_stops=True):
 """Two complete melodic roles plus moving inner-voice accompaniment."""
 result={'h1':[],'h2':[]};melody=melody_rows();owners={};trace=[]
 windplan=json.loads((PIECE/'source/quartet-plan.json').read_text())
 for mi,bar in enumerate(SOURCE['form']):
  section=bar['section'];local=bar['section_bar'];cells={'h1':[],'h2':[]}
  for e in melody[mi]:
   if not e['pitches']:continue
   a=F(e['onset']);b=a+F(e['duration']);ident=e['source_start']
   owner=owners.get(ident)if e['tie_in']else None
   if owner is None:owner=quartet_melody_owner(mi,a)
   owners[ident]=owner;cells[owner].append((a,b,e['pitches'][:],ident))
   trace.append({'bar':mi+1,'onset':str(2*a),'duration':str(2*(b-a)),'owner':owner,'source':ident,'kind':'melody'})
  # These genuinely independent RH notes are present below the source's
  # long C-theme melody. Lower both by one octave, preserving their relation.
  if section=='C'and local in [2,4,10,12]:
   lead=quartet_melody_owner(mi,0);other='h2'if lead=='h1'else 'h1';base=F(2*mi)
   melody_ids={e['source_start']for e in melody[mi]}
   for a,ns in GROUPS[1]:
    if not base<a<base+2:continue
    candidates=[n for n in ns if n['id']not in melody_ids]
    if not candidates:continue
    n=max(candidates,key=lambda x:x['pitch']);b=min(n['b'],base+2)
    cells[other].append((a-base,b-base,[pitch(n['pitch']-12,mi)],n['id']))
    trace.append({'bar':mi+1,'onset':str(2*(a-base)),'duration':str(2*(b-a)),'owner':other,'source':n['id'],'kind':'source_inner_line'})
  if section!='Intro':
   pattern=windplan['counterline_patterns'][section][local-1]
   for onset,duration,tone in pattern:
    a=F(onset)/2;b=a+F(duration)/2
    lead=quartet_melody_owner(mi,a);other='h2'if lead=='h1'else 'h1'
    # Keep the B-register contrast beneath the melody; at its handoff
    # cadence stay near the impending pickup so the new lead does not leap.
    if section=='B'and mi<52 and local not in [8,16]:tone=shifted(tone,-1)
    if mi==51:
     if a!=0:continue
     tone='G4'
    blocked=sorted((x,y)for x,y,_,_ in cells[other])
    if any(x<=a<y for x,y in blocked):continue
    b=min([b]+[x for x,y in blocked if x>a])
    # Do not leave a tiny clipped accompaniment note before a pickup.
    if b-a<F(1,2):continue
    ident=f'quartet-counterline:{mi}:{a}'
    cells[other].append((a,b,[tone],ident))
    trace.append({'bar':mi+1,'onset':str(2*a),'duration':str(2*(b-a)),'owner':other,'source':ident,'kind':'counter_accompaniment'})
  for role in result:
   row=fill_bar(cells[role],mi,76)
   for e in row:
    ident=e['source_start']
    if ident in owners:
     original=next((x for x in melody[mi]if x['source_start']==ident),None)
     if original:e.update(tie_in=original['tie_in'],tie_out=original['tie_out'],source_pitch=original['source_pitch'])
    elif ident is not None:e['velocity']=58 if ident.startswith('quartet-counterline:')else 62
   result[role].append(row)
 # Sparse, deliberate colours. The existing line remains in place; only a
 # second reed is added, with identical onset, duration and velocity.
 from chromatic import double_stop_options
 for bar,role,onset,added,reason in windplan.get('double_stops',[])if with_double_stops else []:
  e=next(e for e in result[role][bar-1]if F(e['onset'])==F(onset)/2 and e['pitches'])
  # If the chosen cadence is already tied across a barline, begin its
  # doubling at the real attack as well. Never break the original sustain.
  chain=[q for es in result[role]for q in es if q['source_start']==e['source_start']]
  for q in chain:
   assert added not in q['pitches']
   sounding=q['pitches']+[added];options=double_stop_options([midi(p)for p in sounding])
   assert options,(bar,role,sounding)
   q.update(pitches=sounding,double_stop={'reason':reason,'added_pitch':added,'fingering':options[0]})
 return result,trace
