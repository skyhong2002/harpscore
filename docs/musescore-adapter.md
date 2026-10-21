# MuseScore 實作與本機經驗

此文件區分可重用方法與當時單曲實作。不要未經能力測試就把本機參數當成所有 MuseScore 版本的標準。

## 已用過的覆層原型

原生音符保留音高、時值、力度供播放，文字顯示固定 C 數字，TextLine 顯示減時線。原生音頭可見但透明，一個和弦只留一個透明 anchor，其餘音頭隱藏且仍可播放，避免透明音頭水平堆疊擠開節奏。

這需要完整映射 native event 到 numeral、accidental、octave dots、duration dots、extension dashes、underline endpoints 與 dynamics。修改原生音符後覆層不會自動正確；必須重建並比對。此 repository 未提供通用 MuseScore 覆層轉換器。

## 經實際畫面調過的起始參數

這些是 Summer v1.0 使用的 profile 起點，不是跨字體、版本的保證。數值是 sp，除非註明 pt。

- 數字 Avenir Next 12pt；Chord x/X/0 用 center,baseline，y=1.0。X 讀既有 velocity >=56，不改 velocity。
- 延音橫線 Avenir Next 13pt、center,baseline、y=0.741；不用 Arial 文字框垂直置中。附點 11.5pt bold。
- 減時線 y=1.32、寬 0.11、起點 offset x=0.60、終點 off2 x=2.36。native anchor 在四分拍整點 leading space 0.75，其他位置 0.4。每拍實際斷口仍須重看。
- 舊 Summer 版的 Dynamics 下方 y=3.8；Chord 在和弦 lane 更下方 y=6.2。五重奏 dynamics 9pt。這是歷史參數；最新 profile 已改 Chord 代號在上方、音桿向下，不能直接把舊座標套到新譜。
- 透明 anchor 的 smallNoteMag=0.6；minNoteDistance=0.55；spacingDensity=1.5。
- 最小小節寬 26；measureSpacing=2.0。依最忙聲部的數字 attack 數，至多四個用 stretch 0.72、五到七個 0.84、其餘 1.0。不是把延音點與「－」當 attacks。
- 五重奏 staff distance 6.1；二重奏 7.6；五重奏一般頁 system distance min 5.4 / max 8.9。首五重奏標題 VBox 55，三大行靠下。
- 段落 offset (-5,-3.2)，小節號對齊 barline、置中，offset (0,-0.7)。首大行有名稱，其後無名稱、無括號，保留連續 barline。
- 最後大行 fill limit 0；不額外 stretch 最後一小節，部分末頁維持正常 system pitch。

## 只對該作品成立的例外

Summer 共 105 小節。H.3 m20 第四拍提早 mf；Chord m99 用八分減少休止；m85 後的音區層次另核對原曲。m99、m102 後加例外換行，保護 m100–102 和 m103–105，因當時 MuseScore 末行放寬最小寬而把六小節擠一起。不能把這些小節號套到新曲。

## 當時 macOS 4.7.5 的限制

正常 MuseScore 視窗可用；CLI -o、-j 匯出曾在 shutdown abort，offscreen 啟動則缺少平台 plugin。該環境不再自動重試 CLI，也不壓掉系統 crash 警告。實際應用名稱或安裝路徑由 agent 在本機查，不寫死私人路徑。

若匯出或開檔造成額外程序，先檢查程序與未存檔，不把兩個 Dock icon 直接當成裝了兩套。已存檔 tab 關閉後再從同一正常視窗開其他譜，是當時可用的操作；不以此否定其他環境正常的多 tab 支援。

PDF 暫停時直接用正常 MuseScore 畫面及截圖檢查，不必另開 SVG 匯出流程。保存後重開，記錄檔案版本及片段位置。容器 ZIP timestamp、內部檔名或縮圖更新不應誤判為音樂改變；須比較有語意的音樂資料。縮圖使用同版實際首頁渲染。

## 八度簡寫與現代播放

僅把八度另一音頭設為 invisible，仍可能由它決定音桿、符尾、連音與附加線；簡譜的原生線也可能留在隱藏五線的舊高度。八度簡寫只在簡譜真實片段試作，檢查升降、連音雙端和換行；五線譜保留兩音。不把「看不見」等同於「不影響排版」，也不將局部原型當成跨曲通用實作。

不要把 stored Note.pitch 與真正播放音高混用。原生 Ottava 可能以較低的儲存音加播放移調表示來源高音；低音譜號的八度符號也須計入。舊版 Events 的裝飾音長度或 GM program 不是新版播放器完整行為。依實際 MuseScore 版本核對啟用的音色資源、現代播放及正常儲存重開，避免修好 XML 卻仍是打擊樂音色。
