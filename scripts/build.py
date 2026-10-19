"""Build portable static handbook and agent packages from canonical Markdown."""
from pathlib import Path
import html
import json
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOCS = [('agent-contract','Agent 執行守則'),('workflow','從新曲開始'),('arranging','配器與可吹性'),('jianpu','簡譜規則'),('preferences','完整偏好'),('conversation-decisions','66 項對話決策'),('musescore-adapter','MuseScore 實作經驗'),('tryout','Agent 試做任務'),('verification','檢查與交付'),('project','維護與發布')]

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
        elif p.is_dir(): shutil.copytree(p,target/p.name)
    records=[]
    canonical={n:(ROOT/n).read_bytes() for n in ['AGENTS.md','SKILL.md']}
    for name,label in DOCS:
        p=ROOT/'docs'/f'{name}.md'
        records.append({'id':name,'label':label,'html':render(p.read_text())})
        canonical[f'docs/{name}.md']=p.read_bytes()
    for p in sorted((ROOT/'profiles').glob('*.json')):
        canonical[str(p.relative_to(ROOT))]=p.read_bytes()
    (target/'docs.js').write_text('window.HANDBOOK='+json.dumps(records,ensure_ascii=False)+';\n')
    for folder in ['docs','profiles','examples']:
        shutil.copytree(ROOT/folder,target/folder)
    shutil.copyfile(ROOT/'AGENTS.md',target/'AGENTS.md')
    shutil.copyfile(ROOT/'SKILL.md',target/'SKILL.md')
    (target/'llms.txt').write_text('# HarpScore\n\nAn agent-readable harmonica arranging and Jianpu skill.\n\nAgent entrypoint: SKILL.md\nContract: docs/agent-contract.md\nFull rules and decisions: llms-full.txt\nTrial task: docs/tryout.md\nProfile: profiles/skyhong.json\nRepository: https://github.com/skyhong2002/harpscore\nDownload: downloads/harpscore-skill.zip\n')
    (target/'llms-full.txt').write_text('\n\n'.join(f'# FILE: {n}\n'+d.decode() for n,d in canonical.items()))
    dl=target/'downloads';dl.mkdir()
    kit={**canonical}
    for folder in ['profiles','examples','agents']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file():kit[str(p.relative_to(ROOT))]=p.read_bytes()
    for n in ['LICENSE','scripts/tryout.py']:kit[n]=(ROOT/n).read_bytes()
    skill={'harpscore/'+n:data for n,data in kit.items()}
    archive(dl/'harpscore-skill.zip',skill)
    archive(dl/'agent-kit.zip',kit)
    import tempfile
    import runpy
    write_fixture=runpy.run_path(str(ROOT/'scripts/tryout.py'))['write_fixture']
    with tempfile.TemporaryDirectory() as temp:
        write_fixture(temp)
        archive(dl/'harpscore-trial.zip',{p.name:p.read_bytes() for p in Path(temp).iterdir() if p.is_file()})
    public={}
    for name in ['README.md','AGENTS.md','SKILL.md','LICENSE','CONTRIBUTING.md','.gitignore']:
        public[name]=(ROOT/name).read_bytes()
    for name in ['docs','profiles','examples','agents','web','scripts','tests','.github']:
        for p in (ROOT/name).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'):
                public[str(p.relative_to(ROOT))]=p.read_bytes()
    archive(dl/'source.zip',public)
    print(f'Built {len(records)} chapters and 4 reproducible download packages in {target}')

if __name__=='__main__': build()
