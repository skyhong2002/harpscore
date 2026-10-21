# HarpScore

**An agent skill for thoughtful harmonica arranging and readable Jianpu in MuseScore.**

HarpScore 的 Harp 呼應 harmonica，Score 致敬 MuseScore。這是一份讓 AI agent 讀取、試做並驗證的口琴編譜能力包；網站是同一份規則的人類閱讀與下載入口。

- Website: https://skyhong2002.github.io/harpscore/
- Agent entrypoint: [SKILL.md](SKILL.md)
- Working contract: [AGENTS.md](AGENTS.md)
- Rules, preferences and decisions: [docs/](docs/)

## Give this to your agent

```text
Use HarpScore: https://github.com/skyhong2002/harpscore
Read SKILL.md and the references it routes to. Use profile skyhong only when I ask
for the founding user's style. First try a representative passage in MuseScore,
verify the actual engraving and playback, then complete the requested work.
Keep source corrections, musical adaptations and layout-only edits separate.
```

已安裝 skill 的 agent 可用 `$harpscore`。其他 agent 可以讀取 repository 的 SKILL.md／AGENTS.md，或取得網站的 `llms-full.txt`、`downloads/harpscore-skill.zip`。核心文件使用可攜的相對路徑；不是只放在某台機器上的私人記憶。

## What is inside

- Agent 守則：何時讀哪些資料、先試做什麼、怎樣才算真的完成。
- 配器與簡譜：樂句交接、初學難度、Bass 延音、Chord 節奏，以及數字、減時線、點、升降與版面。
- 完整偏好與 **對話決策紀錄**：保留修正過程與優先順序，不把被推翻的做法當成預設。
- MuseScore 實作經驗：覆層風險、已用過的起始參數、單曲例外與環境限制分開。
- Summer 實檔版式參考與新曲渲染核對流程。
- 同一來源產生網站、完整 agent 文件包、可安裝 skill 與原始碼下載。

**不是自動聽歌轉譜服務，也尚未包含通用 MuseScore 簡譜渲染引擎。** Skill 的作用是讓 agent 能依可靠規則使用它可用的工具，且對實際成果負責。

## MuseScore 起始檔

[三種編制、六份可編輯譜](templates/musescore/)：《The Entertainer》完整全曲（所有反覆展開，共 152 小節，2/2 拍），含獨奏＋鋼琴、二重奏、四重奏的五線譜與簡譜。獨奏鋼琴簡譜版保留鋼琴大譜表。版式沿用 Summer，雙音縮小對稱置中，弱起與下一句同部承接。正常 MuseScore 渲染與播放已檢查，真人排練仍待進行。原曲／譜源公領域，HarpScore 改編與程式 MIT。見 [使用與驗證](docs/templates.md)。簡譜改音符後仍需同步覆層。

## Try it

在正常 MuseScore 視窗查看實際 Summer 參考檔，複製相符版式，依 [版式驗證流程](docs/tryout.md) 用新曲的代表段落檢查，再完成全曲。原生音符、數字覆層與實際 MuseScore 畫面要互相對得上，不能只檢查 XML；不再生成原創四小節練習。

## Profiles and history

`profiles/fixed-c.json` 是本專案的固定 C 顯示方案。`profiles/skyhong.json` 是使用者的選用偏好。通用規則、個人偏好、Summer 的小節例外及某次 macOS 匯出問題分開維護。

`docs/conversation-decisions.md` 依相關對話順序記錄要求與後續更正，不公開截圖中與製譜無關的私人聊天，也不包含私人檔案路徑。可執行的規則以目前有效決策為準。

## Development

Python 3.9+ 與 Node.js 18+ 用於建置及測試，不需要安裝第三方套件。

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests
node --test tests/brief.test.cjs
python3 -m http.server 8766 --directory dist --bind 127.0.0.1
```

GitHub Actions 驗證後發布 GitHub Pages。編輯 canonical docs 後重建所有下載包，不手動改 dist。完整流程見 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

MIT，適用自行撰寫的程式、文件與原創試做素材。使用者指定展示的 Summer 譜面圖片及其中第三方樂曲除外，見 [NOTICE](web/assets/NOTICE.md)。Repository 不包含其可編輯樂譜、音源或第三方字型。
