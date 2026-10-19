"""Build portable static handbook and agent packages from canonical Markdown."""
from pathlib import Path
import html
import json
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOCS = [('workflow','從新曲開始'),('arranging','配器與可吹性'),('jianpu','簡譜規則'),('verification','檢查與交付'),('project','維護與開發')]

def inline(s):
    s = html.escape(s)
    s = re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    return re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)

def render(md):
    """Render the deliberately small authoring subset used by docs (no raw HTML)."""
    out, para, listing = [], [], False
    def flush():
        if para:
            out.append('<p>'+inline(' '.join(para))+'</p>')
            para.clear()
    for line in md.splitlines():
        if not line.strip():
            flush()
            if listing: out.append('</ul>'); listing=False
        elif line.startswith('#'):
            flush()
            if listing: out.append('</ul>'); listing=False
            level=len(line)-len(line.lstrip('#'))
            out.append(f'<h{level}>'+inline(line[level:].strip())+f'</h{level}>')
        elif line.startswith('- '):
            flush()
            if not listing: out.append('<ul>'); listing=True
            out.append('<li>'+inline(line[2:])+'</li>')
        else: para.append(line)
    flush()
    if listing: out.append('</ul>')
    return '\n'.join(out)

def archive(path, files):
    # Stable timestamps keep generated downloads reproducible.
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):
            item=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(item,data)

def build():
    target=ROOT/'dist'
    if target.exists(): shutil.rmtree(target)
    target.mkdir()
    for p in (ROOT/'web').iterdir():
        if p.is_file(): shutil.copyfile(p,target/p.name)
    records=[]
    canonical={'AGENTS.md':(ROOT/'AGENTS.md').read_bytes()}
    for name,label in DOCS:
        p=ROOT/'docs'/f'{name}.md'
        records.append({'id':name,'label':label,'html':render(p.read_text())})
        canonical[f'docs/{name}.md']=p.read_bytes()
    (target/'docs.js').write_text('window.HANDBOOK='+json.dumps(records,ensure_ascii=False)+';\n')
    for folder in ['docs','profiles','examples']:
        shutil.copytree(ROOT/folder,target/folder)
    shutil.copyfile(ROOT/'AGENTS.md',target/'AGENTS.md')
    (target/'llms.txt').write_text('# Harmonica Arranging\n\nAgent entrypoint: AGENTS.md\nFull handbook: llms-full.txt\nWorkflow: docs/workflow.md\nJianpu: docs/jianpu.md\nProfile: profiles/fixed-c.json\nDownload: downloads/agent-kit.zip\n')
    (target/'llms-full.txt').write_text('\n\n'.join(f'# FILE: {n}\n'+d.decode() for n,d in canonical.items()))
    dl=target/'downloads';dl.mkdir()
    skill={}
    for p in (ROOT/'skills/harmonica-arranging').rglob('*'):
        if p.is_file():skill['harmonica-arranging/'+str(p.relative_to(ROOT/'skills/harmonica-arranging'))]=p.read_bytes()
    for name,_ in DOCS:
        skill[f'harmonica-arranging/references/{name}.md']=(ROOT/'docs'/f'{name}.md').read_bytes()
    skill['harmonica-arranging/references/fixed-c.json']=(ROOT/'profiles/fixed-c.json').read_bytes()
    skill['harmonica-arranging/LICENSE']=(ROOT/'LICENSE').read_bytes()
    archive(dl/'harmonica-arranging-skill.zip',skill)
    kit={**canonical,'profiles/fixed-c.json':(ROOT/'profiles/fixed-c.json').read_bytes(),'examples/brief.json':(ROOT/'examples/brief.json').read_bytes(),'LICENSE':(ROOT/'LICENSE').read_bytes()}
    archive(dl/'agent-kit.zip',kit)
    public={}
    for name in ['README.md','AGENTS.md','LICENSE','CONTRIBUTING.md','.gitignore']:
        public[name]=(ROOT/name).read_bytes()
    for name in ['docs','profiles','examples','skills','web','scripts','tests']:
        for p in (ROOT/name).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'):
                public[str(p.relative_to(ROOT))]=p.read_bytes()
    archive(dl/'source.zip',public)
    print(f'Built {len(records)} chapters and 3 reproducible download packages in {target}')

if __name__=='__main__': build()
