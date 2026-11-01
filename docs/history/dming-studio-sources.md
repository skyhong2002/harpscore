---
title: DMing Studio 教材來源
order: 4
summary: 記錄九支口琴教學的字幕來源、時間點與整理範圍，保留教學內容和取樣驗證的區別。
---

# DMing Studio 教材來源

2026-11-02 依使用者指定，從 [DMing Studio 頻道](https://www.youtube.com/channel/UCJ6wX_ZWY46UzQMYT25MwiA) 選取 Bass、Chord 與半音階口琴教學。這是針對音色與奏法的初始教材集，不是全頻道收錄。來源為蔡明憲／DMing Studio 的教學；HarpScore 的整理與播放實作判準不代表講者為本專案背書。

## 取得與核對範圍

九支影片均用 yt-dlp 取得 YouTube 一般字幕軌中的 zh-TW WebVTT，未使用自動翻譯作為這批教學的依據。一般字幕軌的分類不保證字幕完全無誤。已閱讀字幕與示範前後的文字脈絡；未以此聲稱完成全片視聽、奏法動作觀察或取樣聽驗。

整理後的可執行原則見[口琴音色與奏法](../rules/harmonica-performance.md)；音高、切點、SF2 與 MuseScore 的驗證方法見[取樣與播放](../guide/sound-sampling.md)。嘴型、喉部動作與聲響形容保留為講者的教學方法，不能推定適用所有型號、身體條件或曲風。作品示範不作必修教學，也不以片中的特定曲目建立通用拍型。

| 來源 | 主題與影片 | 發布日期 | 已核對的教學時間 | 對應規則 |
| --- | --- | --- | --- | --- |
| DM01 | [Bass 音色](https://www.youtube.com/watch?v=tZ2sLIl_nxw&t=19) | 2021-07-28 | 0:19–1:43；1:58–2:54 | A22–A23 |
| DM02 | [Bass 喉嚨斷音](https://www.youtube.com/watch?v=C8q0lNLi9kM&t=32) | 2021-08-11 | 0:32–1:52 | A24 |
| DM03 | [Chord 斯洽奏法](https://www.youtube.com/watch?v=QQ-JnW8LKqM&t=19) | 2021-07-07 | 0:19–1:29；2:08–2:40 | A25 |
| DM04 | [Chord 重音](https://www.youtube.com/watch?v=A1w1usba1q8&t=20) | 2021-08-04 | 0:20–1:38 | A26 |
| DM05 | [Chord 喉音](https://www.youtube.com/watch?v=pciczRgPbF0&t=46) | 2021-08-18 | 0:46–1:31；3:25–3:40 | A27 |
| DM06 | [半音階舌斷音](https://www.youtube.com/watch?v=AiXQzo7MWZE&t=15) | 2021-07-10 | 0:15–1:15 | A18 |
| DM07 | [半音階喉嚨斷音](https://www.youtube.com/watch?v=kdjUGMIDPIE&t=18) | 2021-07-24 | 0:18–1:14；3:31–3:49 | A19 |
| DM08 | [半音階嘴型變化](https://www.youtube.com/watch?v=OUeLj0xmFPg&t=24) | 2021-07-31 | 0:24–1:44；3:06–3:49 | A20 |
| DM09 | [半音階喉嚨振音](https://www.youtube.com/watch?v=5fngJzIIxeU&t=20) | 2021-08-07 | 0:20–0:52；2:17–2:51；4:56–5:22 | A21 |

## 示範片段的定位

- DM01 的 1:17 附近由使用者指定為 Bass，字幕在 1:14–1:16 說明將示範較低沉的聲音，1:23 開始下一段說明。這提供取樣上下文，不代替逐音音高與八度核對。2:19–2:25 附近則是偏薄發聲的對照，不能混作同一音色層。
- DM03 的使用者連結從 3:09 開始，但字幕顯示口白持續到約 3:10.306；隨後是奏法示範，約 3:34.596 恢復說明。取樣應檢查實際起音，不能按連結時間直接切出一顆「純和弦」。
- DM08 的 2:09.157–2:13.725 說明低音域較清楚的嘴型，後接示範至約 2:21.632。其他段落有不同嘴型的對照；取樣須保留條件標籤，不把對照組混成同一標準音色。
- 字幕空白只表示沒有該軌的文字，不保證沒有口白、伴奏或其他聲音。上述邊界仍須與音訊核對。

## 字幕重現與保存

需要重新核對時，可將下列命令的 VIDEO_ID 換成表內影片 ID。下載路徑是使用者自行選定的本機來源資料夾，不是可攜式 skill 的必要依賴。

```sh
caption_dir="${TMPDIR:-/tmp}/harpscore-captions"
mkdir -p "$caption_dir"
yt-dlp --skip-download --write-info-json --write-subs \
  --sub-langs zh-TW --sub-format vtt \
  -P "$caption_dir" -o '%(id)s.%(ext)s' \
  'https://www.youtube.com/watch?v=VIDEO_ID'
```

這次原始字幕與取得紀錄保存在 checkout 的 `.openai/local/dming-sources`（git 忽略；不隨網站與 skill 發布）。沒有一般字幕時，先查可用軌道；自動字幕或翻譯必須另標，不能當成講者逐字確認的內容。HTTP 429 等取得失敗記錄為未取得，不反覆重試，也不以影片標題補寫不存在的逐字稿。

下列 SHA-256 對應本次取得的原始 VTT，便於辨認影片字幕日後是否更動；雜湊吻合只證明檔案一致。

| 來源 | VTT SHA-256 |
| --- | --- |
| DM01 | `cfac5dcee78573b56349ed2bc04f72658848f8fe74652e5a30727098119880a4` |
| DM02 | `fc7d22a25d6f17a513eb747682ce05fa3b41863a77a89101eb22290ef8ca53ce` |
| DM03 | `7fefd39fc0ab5d8267b02ebd3a21cb9bb17dae02e1b1817427424197ef3be331` |
| DM04 | `af4aa380ab7cddee5f081e10ba0b43e99212c5e45ecaff0e0f5dd3014017c54e` |
| DM05 | `a340c3c1830558373040a947a3a3fb96b75586883ea738bb5114f3954b61a7d0` |
| DM06 | `bba91883e6ffd52d7dc9ba176edbaaf74b1710604c4fcc95f722f9e1abd22296` |
| DM07 | `316f5350a2bc50ac8e84683618a902f4cf2f0a1559c4d825ac8f72c32ad0da4d` |
| DM08 | `9dc245515a87ba1cbe3a8c6df436d51dd8387acf2901765f96dd8afaaaf6057d` |
| DM09 | `a518c2ae68ae8b4545d88f805149324f5c71739dc52758084879a858a24dbb6f` |

## 權利與證據界線

公開文件是 HarpScore 自行整理的原則與來源索引，並未包含完整第三方字幕、錄音或衍生音色。下載、字幕閱讀、本機切樣、公開散布與實際聽驗是不同事項。影片 metadata 未提供可推定音色再散布的授權；取樣試驗保留在本機，不轉授為 MIT。後續有正式授權時，按授權範圍另記錄，而非回溯假定所有舊素材都可發布。
