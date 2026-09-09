# LINE 私訊觸發推播（Cloudflare Worker）

私訊 Hope Kids Bot「**本週服事夥伴**」→ 卡片自動發到官方群組。

## 一次性設定步驟

1. **建 Worker**：登入 [Cloudflare Dashboard](https://dash.cloudflare.com/)（免費帳號即可）
   → Workers & Pages → Create → Create Worker → 命名（例：`hopekids-line-hook`）→ Deploy
   → Edit code → 把 `line-webhook.js` 全部內容貼上 → Deploy。

2. **建 GitHub PAT**：GitHub → Settings → Developer settings →
   [Fine-grained tokens](https://github.com/settings/personal-access-tokens) → Generate new token
   - Repository access：Only select repositories → `hopekids-bot`
   - Permissions → Repository permissions → **Actions: Read and write**
   - 產生後複製 token（只顯示一次）。

3. **設 Worker 變數**：Worker → Settings → Variables and Secrets，新增四個（型別選 Secret）：
   | 名稱 | 值 |
   | --- | --- |
   | `LINE_CHANNEL_SECRET` | LINE Developers → 該 channel → Basic settings → Channel secret |
   | `LINE_TOKEN` | Messaging API 的 channel access token（跟 GitHub secret 同一組） |
   | `GH_PAT` | 步驟 2 的 token |
   | `ALLOWED_USER_ID` | 先隨便填 `pending`，步驟 5 再改 |

4. **接上 LINE webhook**：LINE Developers → Messaging API 分頁
   - Webhook URL 填 Worker 網址（`https://hopekids-line-hook.<帳號>.workers.dev`）
   - 開啟 **Use webhook**（這次要一直開著，不要再關）
   - LINE Official Account Manager → 回應設定：關閉「自動回應訊息」，避免罐頭回覆。

5. **取得自己的 userId**：用 LINE 私訊 bot「本週服事夥伴」
   → bot 會回你的 userId → 回 Cloudflare 把 `ALLOWED_USER_ID` 改成這串 → 存檔。

6. **再私訊一次「本週服事夥伴」**→ 應回「收到！」→ 約 1 分鐘內卡片出現在群組。

## 安全性

- 驗證 LINE 簽章（Channel secret），偽造請求直接 403。
- 只理「私訊」且內容完全等於關鍵字；群組裡的訊息一律忽略。
- 只有 `ALLOWED_USER_ID` 本人能觸發，其他人私訊只會拿到自己的 userId。

## 追加：line-remind（小組聚會提醒 + 每日計畫，準點排程）

這個 worker 原本只負責 hopekids-bot 的排程，現在多兼兩個 `line-remind` repo 的排程，
取代原本會延遲的 GitHub 原生 `schedule:`：

- 每週二 台北19:00 → `remind.yml`（小組聚會提醒）
- 週一~週五 台北06:00 → `daily_plan.yml`（每日計畫，週末不發）

（這兩個「只在特定星期幾發」的判斷都寫在程式碼裡，Cron Trigger 本身設成每天觸發即可，
細節見下方步驟4的說明。）

兩個排程共用同一組 PAT（`GH_PAT_LINE_REMIND`），因為都是 `line-remind` 這個 repo，
差別只在觸發哪個 workflow 檔案。

### 設定步驟

1. **建第二組 GitHub PAT**（跟 hopekids-bot 的 `GH_PAT`分開，只管 `line-remind` 這個 repo）：
   GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token
   - Repository access：Only select repositories → `line-remind`
   - Permissions → Repository permissions → **Actions: Read and write**
   - 複製 token（只顯示一次）

2. **加 Worker 變數**：Worker → Settings → Variables and Secrets → 新增一個 Secret：
   | 名稱 | 值 |
   | --- | --- |
   | `GH_PAT_LINE_REMIND` | 步驟 1 的 token |

3. **貼上更新後的 `line-webhook.js`**：把這個檔案最新內容整份貼到
   Worker → Edit code，蓋掉舊版 → Deploy。

4. **加兩個 Cron Trigger**：Worker → Settings → Triggers → Cron Triggers → Add Cron Trigger，
   分別新增（⚠️ 兩組都不要加星期幾，Cloudflare 的星期欄位編號跟一般 cron 不同，
   之前試過 `0 11 * * 2` 結果被解讀成週一而不是週二；星期幾的判斷已經寫進程式碼裡了）：
   - `0 11 * * *`（UTC，= 台北每天 19:00；程式碼裡只有週二會真的觸發 remind.yml）
   - `0 22 * * *`（UTC，= 台北每天 06:00；程式碼裡只有週一~週五會真的觸發 daily_plan.yml）

5. 完成後，`line-remind` repo 那邊的 GitHub 原生 `schedule:` 已經全部拿掉了
   （兩個 workflow 都改成只留 `workflow_dispatch`），watchdog.yml 照舊巡檢、漏發自動補發。

⚠️ **在完成上面 4 步之前，這兩個排程完全不會自動觸發**（原生排程已經移除、
Cloudflare 那邊還沒接上），期間只能靠 watchdog 延遲補發或手動觸發，
建議盡快做完這 4 步，愈晚做空窗期愈久。
