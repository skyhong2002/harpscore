const nav=document.getElementById('doc-nav'), content=document.getElementById('doc-content');
for(const [i,doc] of window.HANDBOOK.entries()){
  const b=document.createElement('button'); b.type='button';b.textContent=`0${i+1}  ${doc.label}`;
  b.onclick=()=>{for(const el of nav.children){el.classList.remove('active');el.removeAttribute('aria-current')}; b.classList.add('active');b.setAttribute('aria-current','page'); content.innerHTML=doc.html;};
  nav.appendChild(b);if(i===0)b.click();
}
let currentBrief=null;
const form=document.getElementById('brief-form'),msg=document.getElementById('form-message'),out=document.getElementById('prompt-output');
form.elements.ensemble.onchange=()=>{const hide=form.elements.ensemble.value==='quintet';document.getElementById('piano-option').hidden=hide;if(hide)form.elements.piano.checked=false};
form.onsubmit=e=>{e.preventDefault();try{currentBrief=HarmonicaBrief.makeBrief({title:form.elements.title.value,source:form.elements.source.value,ensemble:form.elements.ensemble.value,level:form.elements.level.value,notation:['staff','jianpu'].filter(n=>form.elements[n].checked),piano:form.elements.piano.checked,pdf:form.elements.pdf.checked,notes:form.elements.notes.value});out.value=HarmonicaBrief.prompt(currentBrief);document.getElementById('result').hidden=false;msg.textContent='需求已產生。請和 Agent 文件包一起提供給你的 agent。'}catch(err){msg.textContent=err.message}};
document.getElementById('copy').onclick=async()=>{try{await navigator.clipboard.writeText(out.value);msg.textContent='已複製協作指令。'}catch{out.focus();out.select();msg.textContent='瀏覽器未允許直接複製，已選取文字，請按複製快捷鍵。'}};
document.getElementById('download').onclick=()=>{if(!currentBrief)return;const blob=new Blob([JSON.stringify(currentBrief,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='arrangement-brief.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)};
