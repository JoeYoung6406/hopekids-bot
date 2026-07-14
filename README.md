# Hope Kids Bot

每週六晚上 20:00（台北時間）自動抓取「當週服事表」Google 試算表，
排成 Hope Kids 品牌風格的 Flex 卡片，推播到 LINE 服事群組。

訊息會以「**Hope Kids Bot**」的名稱與 Hope Kids logo 頭像顯示
（透過 LINE 的 sender 覆寫，寫在 `push_weekly.py` 裡）。

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

## 調整

- **發送時間**：改 `.github/workflows/weekly.yml` 的 cron（注意是 UTC，台北時間減 8 小時）
- **顯示的崗位**：改 `push_weekly.py` 開頭的 `ROLES` 清單
- **Bot 名稱／頭像**：改 `push_weekly.py` 的 `BOT_NAME`、`BOT_ICON`
- **資料來源**：試算表需維持「知道連結的使用者可檢視」，且「當週服事表」分頁
  的日期格式為 `日期：YYYY/MM/DD`、崗位格式為 `崗位：名字`
