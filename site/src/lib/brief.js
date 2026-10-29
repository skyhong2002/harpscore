// Builds an arrangement brief (examples/brief.json shape) and the matching
// agent prompt. Runs in the browser; tested with node --test.

export const ENSEMBLES = {
  solo: '獨奏',
  duet: '二重奏',
  quartet: '四重奏（兩部半音階、DB H.、Chord）',
  quintet: '五重奏（三部半音階、DB H.、Chord）',
};

export const LEVELS = {
  'beginner-2-months': '初學約兩個月',
  intermediate: '中階',
  advanced: '進階',
};

const NOTATIONS = ['staff', 'jianpu'];
const PIANO_ENSEMBLES = ['solo', 'duet'];

export function makeBrief(input) {
  const title = String(input.title || '').trim();
  const source = String(input.source || '').trim();
  if (!title || !source) throw new Error('請填曲名與參考來源。');
  if (!Object.hasOwn(ENSEMBLES, input.ensemble)) throw new Error('請選擇支援的編制。');
  if (!Object.hasOwn(LEVELS, input.level)) throw new Error('請選擇演奏程度。');
  const notation = [...new Set((input.notation || []).filter((n) => NOTATIONS.includes(n)))];
  if (!notation.length) throw new Error('至少選一種記譜方式。');
  const piano = !!input.piano && PIANO_ENSEMBLES.includes(input.ensemble);
  return {
    schema_version: '0.1',
    title,
    source,
    ensemble: input.ensemble,
    level: input.level,
    profile: 'fixed-c',
    editions: piano ? ['combined-harmonicas', 'with-piano-master'] : ['combined-harmonicas'],
    notation,
    pdf: !!input.pdf,
    notes: String(input.notes || '').trim(),
  };
}

export function prompt(brief, version) {
  const notation = brief.notation.map((n) => (n === 'jianpu' ? '固定 C 簡譜' : '五線譜')).join('、');
  const editions = brief.editions.includes('with-piano-master') ? '口琴合併譜與加鋼琴總譜' : '口琴合併總譜';
  const lines = [
    `請依 HarpScore ${version} 的 SKILL.md、AGENTS.md 與相關手冊協作編譜。`,
    '',
    `曲名：${brief.title}`,
    `參考：${brief.source}`,
    `編制：${ENSEMBLES[brief.ensemble]}`,
    `程度：${LEVELS[brief.level]}`,
    `記譜：${notation}`,
    `交付：${editions}，不另拆個別口琴分部。`,
    `PDF：${brief.pdf ? '需要，使用已驗證的匯出方式' : '暫不輸出，先在 MuseScore 檢視'}`,
    '',
    '先確認實際樂器型號與音域。保持完整樂句，依程度分配主旋律與伴奏。簡譜用 quarter-beat 減時線斷口與固定 C profile；演奏音高與顯示八度分開驗證。核對代表段落後完成全曲；純排版修改不動音符、起點、時值與力度。最後提供實際檢查過的項目與尚未驗證之處。',
  ];
  if (brief.notes) lines.push('', `其他需求：${brief.notes}`);
  lines.push('', '請一併讀取我附上的 agent 文件包，不要只依這段短提示詞猜測細節。');
  return lines.join('\n');
}
