"""Build three full Entertainer arrangements in two notation formats each.

The complete source event set is public domain. This is a bounded arrangement,
not a transcription engine. Rendering must be checked in normal MuseScore.
"""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile
import xml.etree.ElementTree as E
sys.path.insert(0,str(Path(__file__).resolve().parent))
from entertainer import edition
from entertainer_notation import fill_score,put,setv
ROOT=Path(__file__).resolve().parents[1]
EDITIONS={'Solo':['h1'],'Solo_Piano':['h1','piano'],'Duet':['h1','h2'],'Duet_Piano':['h1','h2','piano'],'Quintet':['h1','h2','h3','bass','chord']}
CURRENT_FORMS=['Solo_Piano','Duet','Quartet']
def xml(root):
 E.indent(root);return E.tostring(root,encoding='utf-8',xml_declaration=True)
def build_templates(destination,bars=None,forms=None):
 if bars not in [None,152]:raise ValueError('The complete performance contains 152 unfolded bars')
 destination=Path(destination);destination.mkdir(parents=True,exist_ok=True);records=[]
 for form in (forms or CURRENT_FORMS):
  for numbered in ([False,True]if form in ['Solo','Solo_Piano','Duet','Quintet','Quartet']else [False]):
   suffix=form+('_Numbered'if numbered else '');stem='HarpScore_'+suffix
   root=E.parse(ROOT/'templates/layout'/f'{suffix}.mscx').getroot();score=root.find('Score');music=edition(form)
   for k,v in {'workTitle':music['title'],'composer':'Scott Joplin','arranger':'skyhong.tw','copyright':'Scott Joplin composition: Public Domain; HarpScore adaptation: MIT','harpscoreTemplateVersion':'0.3.0','harpscoreOverlayAutoSync':'false','harpscoreScope':'Complete rag; Intro AA BB A CC Bridge DD; all repeats and endings written out','jianpuChromaticUnpointedC':'72','jianpuBassUnpointedC':'48'}.items():put(score,'metaTag',v,name=k)
   graphics=fill_score(root,music,numbered)
   style=E.parse(ROOT/'templates/layout'/f'{suffix}.mss').getroot()
   # Keep Summer's geometry; replace only the old song's running title.
   for key in ['oddHeaderC','evenHeaderC']:
    if style.find('Style/'+key)is not None:setv(style.find('Style'),key,'$:workTitle:')
   if suffix in ['Quintet_Numbered','Quartet_Numbered']:
    # The quartet's moving inner voice needs a larger accidental/dynamic lane.
    for key in ['staffDistance','akkoladeDistance']:setv(style.find('Style'),key,7.5 if suffix=='Quartet_Numbered'else 6.5)
   members={stem+'.mscx':xml(root),'score_style.mss':xml(style)}
   container=E.Element('container');files=put(container,'rootfiles')
   for name in members:put(files,'rootfile',**{'full-path':name})
   members['META-INF/container.xml']=xml(container)
   # Only embed a normal-window preview tied to these exact XML/style bytes.
   # A musical/layout edit automatically invalidates the cached preview.
   previews=ROOT/'templates/previews/manifest.json'
   if previews.exists():
    preview=json.loads(previews.read_text()).get(suffix)
    if (preview and preview['score_xml_sha256']==hashlib.sha256(members[stem+'.mscx']).hexdigest()
            and preview['style_sha256']==hashlib.sha256(members['score_style.mss']).hexdigest()):
     members['Thumbnails/thumbnail.png']=(ROOT/'templates/previews'/preview['file']).read_bytes()
   path=destination/(stem+'.mscz')
   with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED)as z:
    for name,data in sorted(members.items()):
     info=zipfile.ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
   references=destination/'events';references.mkdir(exist_ok=True)
   (references/(form+'.json')).write_text(json.dumps(music,indent=2)+'\n')
   if numbered:(references/(form+'_Numbered_display.json')).write_text(json.dumps(graphics,ensure_ascii=False,indent=2)+'\n')
   records.append({'file':path.name,'form':form,'notation':('numbered-wind-and-staff-piano'if form=='Solo_Piano'else 'numbered')if numbered else 'staff','bars':152,'pickup':False,'staves':len(music['parts']),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'license':'Public Domain composition; MIT adaptation','musical_content':'The Entertainer: complete rag with all repeats and endings','events':f'templates/musescore/events/{form}.json','layout_source':f'templates/layout/{suffix}.mss','verification_record':'templates/verification.json'})
 (destination/'manifest.json').write_text(json.dumps({'version':'0.3.0','templates':records},indent=2)+'\n');return records
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--bars',type=int);p.add_argument('--form',action='append',choices=list(EDITIONS)+['Quartet']);a=p.parse_args();print(json.dumps(build_templates(a.out,a.bars,a.form),indent=2))
