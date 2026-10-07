# Hope Kids Bot

每週六晚上 20:00（台北時間）自動抓取「當週服事表」Google 試算表，
排成 Hope Kids 品牌風格的 Flex 卡片，推播到 LINE 服事群組。

訊息以官方帳號「**Hope Kids Bot**」的名稱與頭像顯示。

## 一次性設定步驟

### 1. 建立 LINE Bot（官方帳號）

1. 到 [LINE Developers Console](https://developers.line.biz/console/)
2. 建立（或沿用）一個 Provider → 建立 **Messaging API** channel，名稱填 **Hope Kids Bot**
3. 在「Messaging API」分頁最下方發行 **Channel access token (long-lived)**，複製起來
4. 在「Messaging API」分頁把「允許加入群組（Allow bot to join group chats）」打開

### 2. 把 Bot 加進群組並取得 Group ID

1. 用 channel 頁面上的 QR code 把 Bot 加為好友，邀進服事群組
2. 取得群組 ID（`C` 開頭的字串）：最簡單的方式是暫時把 Webhook URL 指到
   [webhook.site](https://webhook.site) 產生的網址並開啟 Use webhook，
   然後在群組裡隨便說一句話，webhook.site 上收到的 JSON 裡
   `source.groupId` 就是群組 ID。取完可把 webhook 關掉。
   （之前 line-remind 設定過一次，方法相同）

### 3. 設定 GitHub Secrets

在本機執行（或到 repo Settings → Secrets and variables → Actions 手動加）：

```bash
gh secret set LINE_TOKEN --repo JoeYoung6406/hopekids-bot
gh secret set LINE_GROUP_ID --repo JoeYoung6406/hopekids-bot
```

### 4. 測試

到 repo 的 **Actions → Hope Kids 每週服事表推播 → Run workflow** 手動跑一次，
群組應該會收到卡片。

本機測試（不會真的發送，只印出訊息 JSON 與解析結果）：

```bash
DRY_RUN=1 python push_weekly.py
```

## 追加：第二隻 LINE 帳號輪替（突破免費200則/月額度）

一隻 LINE Official Account 免費方案每月只有 200 則推播額度，用完當月就不能再發。
解法是再建一隻帳號，兩隻帳號依「當天日期單雙號」輪流發送（跟 `line-remind` 的
`send_daily.py` 同一個模式），等於把額度翻倍成 400 則/月。

### 設定步驟

1. **建第二個 LINE Bot**：比照上面「1. 建立 LINE Bot」的步驟，再建一個全新的
   Messaging API channel（名稱可以一樣叫 Hope Kids Bot，或取別的名字都行，
   使用者看到的推播訊息本來就是用同一套卡片樣式，帳號名稱不影響內容）
2. **把這隻也加進同一個服事群組**：用它的 QR code 加好友、邀進跟原本同一個
   LINE 群組（不用重新取得 Group ID，沿用現有的 `LINE_GROUP_ID` 即可，
   因為是推到同一個群組，只是換一隻帳號發）
3. **加第二組 GitHub Secret**：

   ```bash
   gh secret set LINE_TOKEN_B --repo JoeYoung6406/hopekids-bot
   ```

4. 完成後 `push_weekly.py`、`push_unavailable_form.py` 會自動依日期單雙號
   在 `LINE_TOKEN`／`LINE_TOKEN_B` 之間輪替，不用再手動切換。
   如果 `LINE_TOKEN_B` 還沒設定，程式會自動退回用 `LINE_TOKEN`，不會壞掉。

## 調整

- **暫停某一次推播**：把日期（台北時間 `YYYY-MM-DD`）寫進 `skip_dates.txt`，
  例如 `2026-09-30  # 這週停發`。當天排程照常執行，但腳本會直接結束不發送，
  watchdog 也不會判定漏發而補發（SEND_LOG.md 仍會記成 success）。
  兩支推播腳本（服事表、無法服事日期表單）都吃這份清單；過期的日期留著不影響。
- **發送時間**：改 `.github/workflows/weekly.yml` 的 cron（注意是 UTC，台北時間減 8 小時）
- **顯示的崗位**：改 `push_weekly.py` 開頭的 `ROLES` 清單
- **Bot 名稱／頭像**：在 LINE Official Account Manager 的帳號設定裡改
- **資料來源**：試算表需維持「知道連結的使用者可檢視」，且「當週服事表」分頁
  的日期格式為 `日期：YYYY/MM/DD`、崗位格式為 `崗位：名字`
