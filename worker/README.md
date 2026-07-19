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
