---
title: 維護與發布
order: 1
summary: 說明共用規則、可攜式套件與專案發布的維護方式。
---

# 維護 HarpScore 的方式

## 定位

HarpScore 的核心是 AI agent 可讀、可遵循、可試做的 skill。網站只是顯示與分發同一份資料；不以行銷頁或一般人類教學取代 agent 的執行規則。

## 單一來源

根目錄 SKILL.md 負責漸進讀取。docs 是完整規則；profiles 是選用偏好；對話決策記錄每個改變與已被取代的要求。版式以實際 Summer 原檔及其抽出的 `layouts/summer/` 為基準；agent 必須用可用工具真正在 MuseScore 檢查參考和新曲，不生成原創四小節練習。

建置從這些檔案產生網站、llms-full.txt、agent 文件包與可安裝 harpscore skill。Git checkout、skill ZIP 與網站讀取的規則必須同版，不能只有下載包內才存在 skill 要引用的資料。

## 檔案放在哪裡

- 新章節放進 `docs/` 對應的資料夾（guide、rules、engraving、history），frontmatter 寫 `title`、`order`、`summary`。網站目錄、llms-full.txt 與下載包會自動收錄，不改建置程式。
- 規則段落以「編號 · 內容」開頭（如 `J08a · ...`）。網站依此建立錨點與規則索引，內文提到的編號會自動連到定義處。編號一經公開就不重用。
- 每首範例曲在 pieces 底下一個資料夾（如 `pieces/entertainer/`）：`piece.json` 描述版本與檔案，`README.md` 說明製作與驗證範圍，`source/` 放來源事件與配器計畫，`build/` 放這首曲子專用的生成腳本，`scores/`、`events/`、`previews/`、`images/` 放成品。單曲腳本不搬進 `tools/`。
- `tools/` 只放與曲目無關、可隨 skill 安裝後執行的工具；repository 的 scripts 資料夾只放維護用程式（如打包），不隨 skill 發布。
- 共用版式放 `layouts/`，並在其 `provenance.json` 記錄來源雜湊。

## 規則變更

新增修正要指出適用編制、profile 與規則編號，附可重現位置和預期效果。Summer 版式直接對照實檔及使用者曲目；公開資料只用合法授權內容或最小語意案例，不新增原創四小節練習取代要求。通用音樂決策、使用者偏好、單曲特例和環境問題分開。歷史記錄不覆寫，但有效狀態隨新指示更新。

涉及排版，保存改前後音樂事件；涉及音樂，明確列出改變。文法、渲染、應用開啟與播放是不同驗證層。先試做密集與容易失敗的片段，再完成全曲。

## 原型與未來工具

現有單曲試作採原生播放音符加文字／線段覆層，不能當成已完成的通用轉譜器。未來若加入 adapter，應以 pitch、onset、duration、velocity、part 等語意事件產生圖形，不按某首曲子的座標補洞。

核心 skill 可在沒有 adapter 時使用 agent 的其他工具。不要因為沒有全自動引擎，就把工作變成只回覆建議；也不要在缺工具時宣稱已完成實作。

## 發布

Repository 與原創內容採 MIT。GitHub Pages 與下載包由相同提交建置：Astro 網站在 repository 的 site 資料夾，打包程式 package.py 把 skill 原始檔、llms 文件與下載包加入同一個輸出目錄。版本號只寫在根目錄 `VERSION`。發布前跑測試、檢查 skill 相對連結與安裝包、實際瀏覽網站，再核對公開頁面。示例樂曲圖片有獨立 NOTICE，不把第三方樂曲一起轉授 MIT。
