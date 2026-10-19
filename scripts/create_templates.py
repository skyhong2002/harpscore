"""Create original empty MuseScore starters. No source scores, converter or GUI required."""
import argparse
from pathlib import Path
import json
import hashlib
import xml.etree.ElementTree as E
import zipfile

EDITIONS = {
    'Solo': ['h1'], 'Solo_Piano':['h1','piano'],
    'Duet':['h1','h2'], 'Duet_Piano':['h1','h2','piano'],
    'Quintet':['h1','h2','h3','bass','chord'],
}

def add(parent, tag, text=None, **attrs):
    n=E.SubElement(parent,tag,{k:str(v) for k,v in attrs.items()})
    if text is not None:n.text=str(text)
    return n

def xml(root):
    E.indent(root)
    return E.tostring(root,encoding='utf-8',xml_declaration=True)

def style(form,jianpu):
    root=E.Element('museScore',version='4.70');s=add(root,'Style')
    settings={
        'pageWidth':'8.27','pageHeight':'11.69','pagePrintableWidth':'7.0889',
        'pageOddLeftMargin':'.590551','pageEvenLeftMargin':'.590551',
        'pageOddTopMargin':'.590551','pageEvenTopMargin':'.590551',
        'pageOddBottomMargin':'.590551','pageEvenBottomMargin':'.590551',
        'staffDistance':'6.1' if form=='Quintet' else '7.6',
        'minSystemDistance':'5.4','maxSystemDistance':'8.9','maxPageFillSpread':'0',
        'minMeasureWidth':'26','measureSpacing':'2.0','minNoteDistance':'.55',
        'spacingDensity':'1.5','smallNoteMag':'.6','lastSystemFillLimit':'0',
        'startBarlineSingle':'1','startBarlineMultiple':'1',
        'firstSystemInstNameVisibility':'0','subsSystemInstNameVisibility':'2',
        'measureNumberSystem':'1','measureNumberAlignToBarline':'1',
        'measureNumberHPlacement':'center','measureNumberVPlacement':'0',
        'showHeader':'1','headerFirstPage':'0','headerOddEven':'1',
        'oddHeaderL':'','oddHeaderC':'$:workTitle:','oddHeaderR':'',
        'evenHeaderL':'','evenHeaderC':'$:workTitle:','evenHeaderR':'',
        'showFooter':'1','footerFirstPage':'1','footerOddEven':'0',
        'oddFooterL':'','oddFooterC':'$P / $n','oddFooterR':'',
        'evenFooterL':'','evenFooterC':'$P / $n','evenFooterR':'',
        'showPageNumber':'0','footerFontSize':'9','footerAlign':'center,bottom',
        'headerFontSize':'9','harmonyPlacement':'1',
        'musicalSymbolFont':'Leland','musicalTextFont':'Leland Text',
    }
    if jianpu:settings.update({'barNoteDistance':'2.2','noteBarDistance':'2.5'})
    for k,v in settings.items():add(s,k,v)
    add(s,'footerOffset',x=0,y=4)
    add(s,'measureNumberOffset',x=0,y=-.7)
    add(s,'harmonyPosBelow',x=0,y=3.8 if jianpu else 3)
    add(s,'dynamicsPosBelow',x=0,y=3.8 if jianpu else 2)
    return root

def part(score,role,index,staff_start,total_staves,jianpu):
    piano=role=='piano';bass=role=='bass';chord=role=='chord'
    number=role[1:] if role.startswith('h') else ''
    name='Piano' if piano else ('DB H.' if bass else ('Chord' if chord else f'H. {number}'))
    instrument_id='piano' if piano else ('bass-harmonica' if bass else ('concertina' if chord else 'harmonica-c16c'))
    sound_id='keyboard.piano' if piano else ('wind.reed.harmonica.bass' if bass else ('keyboard.concertina' if chord else 'wind.reed.harmonica'))
    p=add(score,'Part',id=index)
    for local in range(2 if piano else 1):
        sd=add(p,'Staff');st=add(sd,'StaffType',group='pitched');add(st,'name','stdNormal')
        if jianpu:
            for tag,val in [('lines',1),('invisible',1),('stemless',1),('clef',0),('keysig',0),('timesig',0),('ledgerlines',0)]:add(st,tag,val)
            add(sd,'barLineFrom',-2);add(sd,'barLineTo',2)
        elif chord:
            add(st,'lines',1);add(st,'clef',0);add(st,'keysig',0);add(st,'ledgerlines',0)
        if piano and local==0:add(sd,'bracket',type=1,span=2,col=0,visible=1)
        add(sd,'barLineSpan',int(staff_start+local<total_staves))
    add(p,'trackName',name)
    ins=add(p,'Instrument',id=instrument_id)
    add(ins,'longName',name);add(ins,'shortName','Pno.' if piano else name);add(ins,'trackName',name)
    low,high=(21,108) if piano else ((28,67) if bass else ((36,93) if chord else (48,98)))
    for key,val in [('minPitchP',low),('maxPitchP',high),('minPitchA',low),('maxPitchA',high)]:add(ins,key,val)
    add(ins,'instrumentId',sound_id)
    if bass:add(ins,'clef','F')
    if piano:add(ins,'clef','F',staff=2)
    art=add(ins,'Articulation');add(art,'velocity',100);add(art,'gateTime',100)
    channel=add(ins,'Channel');add(channel,'program',value=0 if piano else (33 if bass else (21 if chord else 22)))
    add(channel,'controller',ctrl=10,value=63);add(channel,'synti','Fluid')

def text(voice,value,*,size=12,x=.6,y=0,chord=False):
    t=add(voice,'StaffText');add(t,'style','staff');add(t,'family','Avenir Next')
    add(t,'size',size);add(t,'sizeIsSpatiumDependent',0)
    add(t,'align','center,baseline' if chord else 'center,center')
    add(t,'offset',x=x,y=y);add(t,'autoplace',0);add(t,'text',value)
    return t

def score(form,jianpu,bars):
    roles=EDITIONS[form];root=E.Element('museScore',version='4.70')
    add(root,'programVersion','4.7.5');add(root,'programRevision','harpscore-template')
    s=add(root,'Score');add(s,'Division',480)
    for key,val in {'workTitle':'Untitled','composer':'Composer','arranger':'Arranger','copyright':'MIT - HarpScore contributors','harpscoreTemplate':form+('_Jianpu' if jianpu else ''),'harpscoreTemplateVersion':'0.2.0','harpscoreNumeralFont':'Avenir Next','jianpuChromaticUnpointedC':'72','jianpuBassUnpointedC':'48','harpscoreOverlayAutoSync':'false'}.items():add(s,'metaTag',val,name=key)
    staff_roles=[]
    for role in roles:staff_roles.extend([role,'piano-lh'] if role=='piano' else [role])
    start=1
    for i,role in enumerate(roles,1):
        part(s,role,i,start,len(staff_roles),jianpu);start+=2 if role=='piano' else 1
    for si,role in enumerate(staff_roles,1):
        st=add(s,'Staff',id=si)
        if si==1:
            box=add(st,'VBox');add(box,'height',55 if jianpu and form=='Quintet' else (50 if form=='Quintet' else 24));add(box,'boxAutoSize',0)
            for sty,value,size,y in [('title','Untitled',20,0),('subtitle','',11,8),('composer','Composer',9,14),('composer','Arranged by Arranger',9,18)]:
                t=add(box,'Text');add(t,'style',sty);add(t,'size',size)
                if sty=='composer':add(t,'align','right,top')
                add(t,'offset',x=0,y=y);add(t,'text',value)
        for mi in range(bars):
            m=add(st,'Measure');v=add(m,'voice')
            if mi==0:
                clef=add(v,'Clef');add(clef,'concertClefType','F' if role in ['bass','piano-lh'] else 'G');add(clef,'transposingClefType','F' if role in ['bass','piano-lh'] else 'G');add(clef,'isHeader',1)
                key=add(v,'KeySig');add(key,'concertKey',0)
                ts=add(v,'TimeSig');add(ts,'sigN',4);add(ts,'sigD',4)
                if jianpu:
                    for n in [clef,key,ts]:add(n,'visible',0)
                    if si==1:text(v,'4/4',size=9,x=-3.4,y=-2.7)
                if si==1:
                    tempo=add(v,'Tempo');add(tempo,'tempo',2);add(tempo,'followText',1)
                    tx=add(tempo,'text');add(tx,'sym','metNoteQuarterUp').tail=' = 120'
                    if jianpu:add(tempo,'autoplace',0);add(tempo,'offset',x=0,y=-2.4)
            if jianpu:
                for beat in range(4):
                    text(v,'0',y=1 if role=='chord' else 0,chord=role=='chord')
                    if beat<3:loc=add(v,'location');add(loc,'fractions','1/4');add(loc,'timeTick',1)
                loc=add(v,'location');add(loc,'fractions','-3/4');add(loc,'timeTick',1)
            rest=add(v,'Rest');add(rest,'durationType','measure');add(rest,'duration','1/1')
            if jianpu:
                add(rest,'visible',1);add(rest,'color',r=255,g=255,b=255,a=0);add(rest,'small',1)
                seg=add(v,'Segment');add(seg,'leadingSpace',.75)
            if mi==bars-1:
                b=add(v,'BarLine');add(b,'subtype','end')
    return root

def build_templates(destination,bars=12):
    if bars<4:raise ValueError('Use at least four bars')
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    records=[]
    for form in EDITIONS:
        for jianpu in ([False,True] if form in ['Solo','Duet','Quintet'] else [False]):
            stem='HarpScore_'+form+('_Jianpu' if jianpu else '')
            members={stem+'.mscx':xml(score(form,jianpu,bars)),'score_style.mss':xml(style(form,jianpu))}
            c=E.Element('container');files=add(c,'rootfiles')
            for name in members:add(files,'rootfile',**{'full-path':name})
            members['META-INF/container.xml']=xml(c)
            path=destination/(stem+'.mscz')
            with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED)as z:
                for name,data in sorted(members.items()):
                    info=zipfile.ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
            records.append({'file':path.name,'form':form,'notation':'jianpu' if jianpu else 'staff','bars':bars,'staves':sum(2 if r=='piano' else 1 for r in EDITIONS[form]),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'license':'MIT','musical_content':'empty rests only; no third-party music','verification_record':'templates/verification.json'})
    (destination/'manifest.json').write_text(json.dumps({'version':'0.2.0','templates':records},ensure_ascii=False,indent=2)+'\n')
    return records

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--bars',type=int,default=12)
    args=parser.parse_args();print(json.dumps(build_templates(args.out,args.bars),indent=2))
