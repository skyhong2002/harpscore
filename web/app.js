const nav=document.getElementById('doc-nav'), content=document.getElementById('doc-content');
for(const [i,doc] of window.HANDBOOK.entries()){
  const b=document.createElement('button'); b.type='button';b.textContent=`${String(i+1).padStart(2,"0")}  ${doc.label}`;
  b.onclick=()=>{for(const el of nav.children){el.classList.remove('active');el.removeAttribute('aria-current')}; b.classList.add('active');b.setAttribute('aria-current','page'); content.innerHTML=doc.html;};
  nav.appendChild(b);if(i===0)b.click();
}
let currentBrief=null;
const form=document.getElementById('brief-form'),msg=document.getElementById('form-message'),out=document.getElementById('prompt-output');
form.elements.ensemble.onchange=()=>{const hide=form.elements.ensemble.value==='quintet';document.getElementById('piano-option').hidden=hide;if(hide)form.elements.piano.checked=false};
form.onsubmit=e=>{e.preventDefault();try{currentBrief=HarpScoreBrief.makeBrief({title:form.elements.title.value,source:form.elements.source.value,ensemble:form.elements.ensemble.value,level:form.elements.level.value,notation:['staff','jianpu'].filter(n=>form.elements[n].checked),piano:form.elements.piano.checked,pdf:form.elements.pdf.checked,notes:form.elements.notes.value});out.value=HarpScoreBrief.prompt(currentBrief);document.getElementById('result').hidden=false;msg.textContent='需求已產生。請和 Agent 文件包一起提供給你的 agent。'}catch(err){msg.textContent=err.message}};
document.getElementById('copy').onclick=async()=>{try{await navigator.clipboard.writeText(out.value);msg.textContent='已複製協作指令。'}catch{out.focus();out.select();msg.textContent='瀏覽器未允許直接複製，已選取文字，請按複製快捷鍵。'}};
document.getElementById('download').onclick=()=>{if(!currentBrief)return;const blob=new Blob([JSON.stringify(currentBrief,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='arrangement-brief.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)};
document.getElementById('site-search').onsubmit=e=>{
  e.preventDefault();
  const q=document.getElementById('search-input').value.trim().toLocaleLowerCase();
  const status=document.getElementById('search-status');
  status.hidden=false;
  if(!q){status.textContent='請輸入想找的編曲或記譜關鍵字。';return;}
  const matches=window.HANDBOOK.map((d,i)=>({d,i})).filter(({d})=>{
    const temp=document.createElement('div');temp.innerHTML=d.html;
    return temp.textContent.toLocaleLowerCase().includes(q);
  });
  if(!matches.length){status.textContent=`找不到「${document.getElementById('search-input').value.trim()}」，可試試「減時線」、「Bass」或「音域」。`;return;}
  nav.children[matches[0].i].click();
  status.textContent=`找到 ${matches.length} 個章節：${matches.map(x=>x.d.label).join('、')}。已開啟第一個符合的章節。`;
  document.getElementById('handbook').scrollIntoView({behavior:'smooth'});
};
