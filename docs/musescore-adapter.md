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

## 隱藏播放元素與乾淨編輯畫面

透明 Note／Rest 不保證其原生附點也透明。在已驗證的 4.7.5 寫入格式中，可對對應的 `NoteDot` 子物件明示 `visible=0`；保留原本的 `dots` 時值屬性，並逐項核對覆層附點及八度點。其他版本先驗證讀寫器和實際字形，不能只因 XML 看似合理便批次套用。

`noStem` 與隱藏 Note 也不保證輔助 voice 的 Beam 不被排出。多 voice 和弦播放需保留每個簧音與起訖，僅對隱藏的輔助節奏容器設定不生成 Beam；主顯示 voice 的符桿、符尾和節奏不動。不要以刪掉輔助發聲音簡化畫面。

灰色休止、Tuplet 數字、隱藏連線與五線可能只是「顯示隱藏元素」的編輯提示。使用者要求乾淨編輯模式時，關閉該顯示並正常儲存、重開；本次已驗證的每譜設定為 `Score/showInvisible=0`。這只控制編輯提示，不能拿來掩蓋仍會印出的黑色附點或 Beam。分別比較開啟／關閉提示的畫面，記錄同一實檔雜湊。

## 排密後重新定位線條

先依最忙聲部的實際 attack 密度調整小節伸縮與每大行容量，再以正常視窗確認真正的換行。不要只由預計的 LayoutBreak 清單推論頁數或行數。原本按舊大行保存的 Slur／Tie 分段與手動控制點，換行後可能造成凹弧、尖角或續段跑位；必須依新版實際字形與大行重做定位，不能只把整條線平移。

本機 4.7.5 試作以唯讀 plugin 取得已載入譜的字形邊界與大行位置，未匯出媒體。完整走訪各小節的 segments 與所有相關聲部，不能只用第一個 track 的 cursor 取樣，否則會漏掉其他聲部獨有的起音及 tie。根 spanner 的 autoplace 關閉也不保證生成的每個 segment 都採用同樣設定；以實際 renderer 與正常儲存重開為準。這是經驗方法，不是本 repository 已提供通用 plugin 或轉譜引擎的宣告。

三連音橫桿、獨立數字標籤、八度虛線及漸強／漸弱各自保有原生時間範圍。縮短它們與本部數字的距離時，同時檢查升降記號、弧線、前一部及上一大行的末部；固定的全曲 y 值不是驗收。保存後比對有語意的資料；相同時間上的 spanner 序列或依聲部身分對應的 audio track 陣列可能只改序，不能因此忽略成員內容、錯把重複音去重，或把真正的播放改變當成格式差異。
