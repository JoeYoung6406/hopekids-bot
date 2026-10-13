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

## 備用帳號：A 帳號額度用完時，暫時改用 B 帳號

免費方案每月 200 則，而且**推播到群組是按群組人數計費**（25 人的群組推一次＝扣 25 則），
所以某個月推得比較多就可能爆量。這時可以暫時改用第二隻官方帳號（B）發送。

限制：**LINE 一個群組同時只能有一隻官方帳號**，所以兩隻不能同時待在群組裡輪流發，
只能「整個月換成 B」，下個月再換回 A。

### 切換到 B（例：10 月爆量）

1. **在 `account_b_months.txt` 加上月份**（例如 `2026-10`），推上 GitHub。
   列在檔案裡的月份用 B，其他月份自動用 A，不用改程式。
2. **建 B 帳號**（只有第一次需要）：比照上面「1. 建立 LINE Bot」再建一個 Messaging API
   channel，發行 channel access token，然後：

   ```bash
   gh secret set LINE_TOKEN_B --repo JoeYoung6406/hopekids-bot
   ```

3. **在 LINE 群組換 bot**：先把 A 帳號移出群組，再邀 B 帳號進來。
4. **取得 B 看到的 Group ID**：B 的 Webhook URL 暫時指到 [webhook.site](https://webhook.site)
   並開啟 Use webhook，B 一加入群組就會收到 `join` 事件，裡面的 `source.groupId`
   就是它。（LINE 的 ID 會依帳號所屬的 provider 而不同，B 看到的群組 ID 不一定跟 A 一樣，抓一次最保險。）

   ```bash
   gh secret set LINE_GROUP_ID_B --repo JoeYoung6406/hopekids-bot
   ```

   沒設 `LINE_GROUP_ID_B` 的話會沿用 `LINE_GROUP_ID`。

如果某個月列為 B 卻沒有 `LINE_TOKEN_B`，推播會直接失敗（GitHub 會寄信），不會偷偷改用 A。

### 換回 A（例：11 月）

月份不在 `account_b_months.txt` 裡就自動用 A，程式不用動；但**月初第一次推播前**要在
LINE 群組把 B 移出、把 A 邀回來（A 回到同一個群組，原本的 `LINE_GROUP_ID` 照用）。

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
