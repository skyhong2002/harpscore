---
title: 和弦代號字距
order: 4
summary: 以 MuseScore 原生文字邊界計算升降記號間距，保留主字型並批次產生副本。
---

# 簡譜和弦代號的升降記號字距

`tools/chord_spacing.py` 將完整的手動 StaffText 和弦標籤拆成根音、升降記號與後綴，保留主字型，依 MuseScore 已排出的原生文字邊界計算間距。適用 J10a 所述的代號層；不改和聲、拍點、原生音符或播放設定。這是可攜式的批次排版工具，不是完整轉譜器。

## 適用範圍

- 輸入為 `.mscx` 或 `.mscz`，指定一個或多個聲部的完整 StaffText 標籤，例如 `A♭7`、`F♯dim`、`E♭maj7/B♭`。ASCII `b`／`#` 的拼法會保留；後綴內的變化音仍留在後綴，不另解釋和聲。
- 只處理含根音或斜線低音升降記號、可見、關閉 autoplace 的普通 StaffText。可含 `<font face="…"/>` 字型切換；主字型取明確 `--font`、元素 family、第一個內嵌字型或 StaffText 樣式，依序選用。升降記號的字型由 `--accidental-font` 指定，預設 Arial。字級沿用原標籤。
- 一般大小譜表、Staff 文字樣式、無框線及普通字重。自訂文字樣式、粗斜體、內嵌字級／上標、縮小譜表、StaffTypeChange、自動避讓、連結物件與帶播放控制的文字列為 skipped。其他未辨識屬性也不複製拆開，以免重複觸發語意。這些項目需要其他 adapter，不能先攤平成普通文字。
- 原生 Harmony、沒有升降的和弦、簡譜數字、八度點、tr 及其他文字不修改。請由 agent 盤點正確聲部，不能把全譜所有文字當成和弦。

已拆成多個物件的舊譜不猜測還原。工具再跑不會累加位移；要換字距或字型，從保留完整標籤的來源重新產生。輸出物件沒有即時群組同步：之後改和弦內容或拍點，應回到完整來源更新，再跑流程，避免只改其中一個字。

## Agent 執行流程

先依[試做流程](../guide/tryout.md)確認所選參考與當前曲目的版式。安裝、量測、套用與畫面檢查由 agent 完成，不把工具指令交給使用者當成已完成修譜。以下指令從 skill 根目錄執行，所有輸出用不存在的新檔名。

### 1. 建立量測副本

```sh
python3 tools/chord_spacing.py prepare input.mscz chord-metrics-request.json --probe chord-probe.mscz --staff 4
```

`--staff` 從 1 起算，可重複指定。`--font` 可指定主字型；預設保留。`--gap-pt` 預設 0.9 pt，代表相鄰文字 run 原生框之間的水平淨距，不是整個和弦的字元間距。這是初始排版值，仍須按字級與實際畫面驗證。

prepare 盤點全曲選定聲部，產生 request 與量測譜副本。量測副本只把各文字 run 拉開，以便讀取它們的原生邊界；它不是交付譜。request 包含來源 SHA-256、聲部選擇、字型／字級與每個原生樣本的位置。先閱讀 targets 與 skipped；略過不代表已修好。

### 2. 在 MuseScore 讀取原生邊界

將 `plugins/HarpScoreChordMetrics/` 整個資料夾複製到 MuseScore 使用者插件目錄，在 Manage plugins 啟用。把 request 複製為插件旁的 `chord-metrics-request.json`，在正常 MuseScore 視窗開啟剛建立的量測副本，從 Composing/arranging tools 執行 HarpScore Chord Metrics。

外掛只讀取目前譜的 StaffText.bbox，不改譜、不匯出媒體。它確認 probe 身分、已安裝字型及指定文字／字級／座標，將 `chord-metrics.json` 寫在插件旁，會覆寫上次量測；立即複製回作品工作目錄。`error` 必須為 null，backend 必須是 `native StaffText.bbox`。外掛更新後若仍輸出舊 backend，正常關閉重開 MuseScore 再試；僅 Reload plugins 可能仍使用程序內快取，不要反覆套用舊結果。

不能改用一般 Qt TextMetrics 或其他字型庫的 bounding box 代替。即使在同一個 MuseScore 程序內，一般文字的左側 bearing 與譜面 StaffText 的替代字形／邊界處理也可能不同，足以讓拆開的升降記號重疊。字型存在不代表每個 glyph 一定由該字型提供；量測的是當前 renderer 最後排出的結果，仍要看圖確認字形。

### 3. 依量測產生候選

```sh
python3 tools/chord_spacing.py apply input.mscz chord-metrics.json output.mscz --report chord-spacing-report.json
```

apply 核對來源雜湊、完整盤點、probe 身分與量測清單。來源改過就重新 prepare；換 MuseScore、字型或環境也要重新量測，不能跨機沿用。副本保留第一個 run 原本的 offset 作為左對齊原點，再以原生邊界逐個加入淨距。原本若是置中標籤，這會改變整組相對於拍點的視覺左右分布；整組寬度也會改變，不能宣稱原置中外框保持不變。

主字型與升降字型分開設定，不必逐和弦手調 x。新增 run 由正常存檔分配原生 ID；原標籤 ID 留給第一個 run。工具只寫選定文字，其他 MSCZ 成員內容保留。report 的 `visual_acceptance` 固定為 false，表示計算完成不等於畫面驗收。

### 4. 實際驗證

正常存檔、關閉並重開候選。依 V25 檢查全曲同類位置，至少放大查看降記號、升記號、長後綴、斜線低音（若有）、密集節奏及行末；每一種實際出現的字型與字級都要有代表段。看根音與記號、記號與後綴的白縫，也看減時線、鄰近代號、力度、下一聲部與分頁。

保留完整音樂與非目標排版差分，確認 pitch、onset、duration、velocity 及播放設定不變。正常儲存可補新 ID、重排文字屬性順序、省略預設 left alignment 及將 offset 小數序列化捨入；逐項核對範圍與誤差，不直接忽略全部文字差異。可用 [HarpScore Geometry](adaptive-spacing.md)核對最終每組邊界，但幾何間隔不能取代實際截圖。只抽查代表段時明示範圍，不宣稱所有曲目都已通過；本流程不自行恢復已暫停的 PDF 或音訊匯出。
