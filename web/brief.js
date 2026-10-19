(function(root) {
  function makeBrief(input) {
    const title = String(input.title || '').trim();
    const source = String(input.source || '').trim();
    if (!title || !source) throw new Error('請填曲名與參考來源。');
    if (!['solo','duet','quintet'].includes(input.ensemble)) throw new Error('請選擇支援的編制。');
    if (!['beginner-2-months','intermediate','advanced'].includes(input.level)) throw new Error('請選擇演奏程度。');
    const notation = (input.notation || []).filter(x => ['staff','jianpu'].includes(x));
    if (!notation.length) throw new Error('至少選一種記譜方式。');
    return {schema_version:'0.1',title,source,ensemble:input.ensemble,level:input.level,
      profile:'fixed-c',editions:input.piano && input.ensemble !== 'quintet' ? ['combined-harmonicas','with-piano-master'] : ['combined-harmonicas'],
      notation:[...new Set(notation)],pdf:!!input.pdf,notes:String(input.notes || '').trim()};
  }
  function prompt(b) {
    const en={solo:'獨奏',duet:'二重奏',quintet:'五重奏（三部半音階、DB H.、Chord）'};
    const lv={'beginner-2-months':'初學約兩個月',intermediate:'中階',advanced:'進階'};
    return `請依 HarpScore 0.1.0 的 SKILL.md、AGENTS.md 與相關手冊協作編譜。\n\n曲名：${b.title}\n參考：${b.source}\n編制：${en[b.ensemble]}\n程度：${lv[b.level]}\n記譜：${b.notation.map(n=>n==='jianpu'?'固定 C 簡譜':'五線譜').join('、')}\n交付：${b.editions.includes('with-piano-master')?'口琴合併譜與加鋼琴總譜':'口琴合併總譜'}，不另拆個別口琴分部。\nPDF：${b.pdf?'需要，使用已驗證的匯出方式':'暫不輸出，先在 MuseScore 檢視'}\n\n先確認實際樂器型號與音域。保持完整樂句，依程度分配主旋律與伴奏。簡譜用 quarter-beat 減時線斷口與固定 C profile；演奏音高與顯示八度分開驗證。核對代表段落後完成全曲；純排版修改不動音符、起點、時值與力度。最後提供實際檢查過的項目與尚未驗證之處。${b.notes?'\n\n其他需求：'+b.notes:''}\n\n請一併讀取我附上的 agent 文件包，不要只依這段短提示詞猜測細節。`;
  }
  const api={makeBrief,prompt};
  if (typeof module!=='undefined' && module.exports) module.exports=api;
  else root.HarpScoreBrief=api;
})(globalThis);
