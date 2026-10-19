# Harmonica Arranging

口琴編曲、五線譜與簡譜的開放協作手冊。給演奏者、編曲者，以及和他們一起工作的 agent。

目前是 **0.1.0 協作規範與網站雛形**：已有可閱讀的 SOP、規則編號、需求範本、agent skill 與需求產生器。尚未提供通用音源轉譜或 MuseScore 自動編譜引擎。現有單曲製譜程式仍需另外重構，不能直接套用任意歌曲。

## 使用

1. 從網站建立需求，或填寫 `examples/brief.json`。
2. 將需求和 `AGENTS.md` 交給 agent；需要簡譜時一起提供 `docs/jianpu.md`。
3. 先核對音樂，再檢查排版與播放。網站不接收或上傳音源。

給 agent 的起始指令：

```text
閱讀這個專案的 AGENTS.md，使用 docs/workflow.md 與 docs/arranging.md。
簡譜另讀 docs/jianpu.md。依我提供的需求做完整曲目，先核對代表段落。
把音樂變更和純排版變更分開記錄；不要自行把簡譜升降改成首調。
```

## 本機開發

只需要 Python 3 與現代瀏覽器，沒有 Node 套件安裝步驟。

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests
python3 -m http.server 8766 --directory dist --bind 127.0.0.1
```

`docs/*.md` 是手冊的唯一來源；建置會產生網站、`llms-full.txt` 和 agent ZIP，不需要手動同步三份內容。`web/brief.js` 同時供網站和 Node 測試使用。

## 專案結構

- `docs/`：編曲、簡譜、驗收與維護規則。
- `profiles/`：可選的風格設定；個人偏好不等於所有口琴譜的標準。
- `skills/harmonica-arranging/`：可安裝的 agent 入口，建置時附上同版手冊。
- `examples/`：不含既有歌曲音符的需求範例。
- `web/`：網站介面與需求產生器。
- `scripts/build.py`：無相依套件的靜態網站與 agent 文件建置。
- `tests/`：文件連結、發布內容、建置一致性與需求產生器檢查。

## 開放維護

程式與自行撰寫的文件採 MIT 授權，見 `LICENSE`。第三方樂曲、錄音、字型和範例譜不因此取得授權；目前不收錄它們。歡迎提交有可重現範例的規則修訂，見 `CONTRIBUTING.md`。需要跨作品驗證的規則會標示為設定檔或實驗性做法。

下一階段優先使用第二首曲子驗證規則，建立原創短小測試樂句，再抽離 MuseScore adapter、節奏模型與排版檢查。不要把某首曲子的第 20、99 或 102 小節例外搬進通用引擎。
