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
- [自適應部距](docs/engraving/adaptive-spacing.md)：依實際字形計算局部最小部距，附幾何讀取插件與可攜式工具。
- MuseScore 實作經驗：覆層風險、已用過的起始參數、單曲例外與環境限制分開。
- 依編制與記譜方式選擇版式，對照參考實檔並核對新曲渲染。
- 同一來源產生網站、完整 agent 文件包、可安裝 skill 與原始碼下載。

**不是自動聽歌轉譜服務，也尚未包含通用 MuseScore 簡譜渲染引擎。** Skill 的作用是讓 agent 能依可靠規則使用它可用的工具，且對實際成果負責。

## MuseScore 起始檔

依 [編制與記譜版式](docs/guide/starting-a-piece.md) 選擇獨奏、鋼琴伴奏或重奏的起始配置，再以當次任務的來源建立音樂。五線譜、簡譜與口琴簡譜搭配鋼琴大譜表各有對應的顯示方式；原生譜、音樂事件與驗證紀錄分開保存。簡譜改音符後仍需同步覆層。教學流程不要求使用任何特定曲目。

## Try it

在正常 MuseScore 視窗查看所選版式的實際參考檔，複製相符版式，依 [版式驗證流程](docs/guide/tryout.md) 用新曲的代表段落檢查，再完成全曲。原生音符、數字覆層與實際 MuseScore 畫面要互相對得上，不能只檢查 XML；不再生成原創四小節練習。

## Profiles and history

`profiles/fixed-c.json` 是本專案的固定 C 顯示方案。`profiles/skyhong.json` 是使用者的選用偏好。通用規則、個人偏好、特定作品的小節例外及某次 macOS 匯出問題分開維護。

`docs/history/conversation-decisions.md` 依相關對話順序記錄要求與後續更正，不公開截圖中與製譜無關的私人聊天，也不包含私人檔案路徑。可執行的規則以目前有效決策為準。

## Repository layout

```text
SKILL.md, AGENTS.md   agent 入口與工作守則
docs/                 手冊：guide 開始、rules 規則、engraving MuseScore 工法、history 偏好與決策
profiles/             顯示方案與選用偏好
layouts/              共用版式、聲部設定、字形樣板與來源紀錄
pieces/<id>/          每首範例曲：piece.json、來源、生成腳本、MSCZ、事件、預覽與驗證紀錄
tools/                可攜式通用工具（幾何、碰撞、部距）
plugins/              MuseScore 幾何讀取插件
scripts/package.py    產生 llms 文件與下載包
site/                 Astro 網站，直接讀取 docs/ 與 pieces/
```

## Development

Python 3.9+（只用標準函式庫）負責測試與打包；網站需要 Node.js 22.23.4 以上（見 `site/.node-version`）。

```sh
python3 -m unittest discover -s tests
cd site && npm ci && npm run build && npm test
npx astro preview      # http://localhost:4321/harpscore/
```

`npm run build` 先建置網站，再由 `scripts/package.py` 把 skill 檔案、`llms-full.txt` 與下載包放進 `site/dist`。新增章節或曲目不需要改建置程式：章節靠 frontmatter，曲目靠 `piece.json`。GitHub Actions 在 main 驗證後發布 GitHub Pages。完整流程見 [CONTRIBUTING.md](CONTRIBUTING.md) 與 [維護與發布](docs/maintaining.md)。

## License

MIT，適用自行撰寫的程式、文件與原創試做素材。使用者指定展示的 Summer 譜面圖片及其中第三方樂曲除外，見 [NOTICE](site/public/images/summer/NOTICE.md)。Repository 不包含其可編輯樂譜、音源或第三方字型。
