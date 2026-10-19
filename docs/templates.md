# MuseScore 原生起始檔（實驗性）

HarpScore 附上八份 `.mscz` 原生起始檔，放在 `templates/musescore/`。這些檔案由本專案自行生成，只有十二個空白小節，沒有 Summer 或其他第三方歌曲的音符、圖片與錄音，採 MIT。

## 五線譜：五份

- HarpScore_Solo.mscz：一部半音階。
- HarpScore_Solo_Piano.mscz：一部半音階與雙譜表鋼琴。
- HarpScore_Duet.mscz：兩部半音階，放在同一份合奏譜。
- HarpScore_Duet_Piano.mscz：兩部半音階與雙譜表鋼琴。
- HarpScore_Quintet.mscz：三部半音階、DB H. 與單線 Chord。

## 簡譜：三份

- HarpScore_Solo_Jianpu.mscz：一部半音階。
- HarpScore_Duet_Jianpu.mscz：兩部半音階。
- HarpScore_Quintet_Jianpu.mscz：三部半音階、DB H. 與 Chord。

簡譜預先設置隱藏原生譜表與數字覆層，空白小節每拍顯示 0，供 agent 從現成結構開始。**修改或輸入原生音符不會自動更新數字。** Agent 必須同步改寫數字、八度點、升降與減時線，再比對原生音符與實際畫面。它不是會自動轉換音符的 MuseScore 簡譜外掛；直接輸音符後仍顯示 0 不能當成譜已完成。

## 預先設定了什麼

- A4、4/4、四分音符 = 120、C 大調作為中性起點；新曲先確認調性與速度。
- 每小節最小寬 26 sp、自然換行、行首小節線及跨聲部小節線、名稱僅首大行顯示。
- 第二頁起頁首讀取 workTitle；頁腳置中顯示「頁數 / 總頁數」，斜線兩旁有空格。
- 空白曲名與署名佔位，沒有某首曲子的作者或來源說明。修改首頁曲名與 score properties 的 workTitle，讓頁首一致。
- 半音階預設發聲 C3–D7、DB H. E1–G4，供十六孔／double bass 配器試做；這不是所有實體樂器的共同音域，編曲前仍依實際型號確認。
- 簡譜無點 1 的參考為半音階 C5、DB H. C3；文字覆層使用 Avenir Next。沒有這個字型的機器請換可取得的單線筆畫字型，再檢查字寬、底線與基線。檔案不附帶字型。
- Chord 使用普通圓形音頭的單線五線譜；簡譜版的 0 使用與未來 x/X 相同的 baseline 設定。空白範本沒有既定和弦，不預填每小節 C 和弦。
- 通用 GM 音色，不含 Muse Sounds 資源、私人帳號或音效外掛路徑。沒有音符的空白範本不提供音色起音品質證據。

## 給 agent 的使用順序

先複製相符編制另存為新曲，改 title、workTitle、composer、arranger、key、meter 和 tempo，再讀所選 profile。輸入核對過的音樂；簡譜要同步覆層。用原創試做素材或新曲代表片段檢查，不把十二個空白小節可開啟誤當成密集節奏排版已驗證。

驗收分成容器/XML、空白音樂結構、正常 MuseScore 視窗載入、實際排版與播放等層。範本的實際正常視窗驗證狀態見 `templates/verification.json`，以對應檔案雜湊為準；沒有驗過的部分不宣稱通過。

目前八份通過容器與空白結構測試；三份簡譜，以及五線譜獨奏、獨奏＋鋼琴，已在 MuseScore 4.7.5 正常視窗載入並目視檢查。另三份五線譜待正常視窗檢查，仍標為實驗性。空白範本尚未驗證密集音符、播放起音或匯出品質。編輯器中的灰色譜線是隱藏譜表的編輯輔助；首次開啟可能標示未儲存，請另存新曲。

## 維護與重建

執行 `python3 scripts/create_templates.py --out templates/musescore` 可重建。產生器不讀本機既有樂譜，也不啟動 MuseScore 或輸出 PDF。修改產生器後，重新驗證 native window，保存新的檔案雜湊，才更新該項紀錄。

頁首 metadata 語法參考 MuseScore 官方手冊：https://handbook.musescore.org/text/header-and-footer 。模板的 `$:workTitle:` 只讀取 score properties，不保證與首頁文字框自動雙向同步。
