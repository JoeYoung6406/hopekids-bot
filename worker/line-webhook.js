/**
 * Hope Kids Bot — LINE Webhook + 排程 dispatcher (Cloudflare Worker)
 *
 * 私訊 bot「本週服事夥伴」→ 觸發 GitHub Actions 的 weekly.yml
 * → 服事卡片推播到官方群組（約 30~60 秒）。
 *
 * 另外也身兼「準點排程 dispatcher」：GitHub 原生 schedule 常常整點延遲數小時，
 * 改用 Cloudflare 的 Cron Trigger（很準時）在指定時間呼叫 GitHub 的
 * workflow_dispatch API，等於用 Cloudflare 的時鐘取代 GitHub 的時鐘。
 * 目前掛在這個 worker 上的排程（Cloudflare 的星期欄位跟一般 cron 不同又愛驗證失敗，
 * 所以全部改成「每天觸發」，星期幾要不要發交給 scheduled() 裡的 JS 判斷）：
 *   - 每天 台北10:00（cron 0 2 * * *）  → hopekids-bot repo（依星期/日期判斷要不要發）
 *   - 每天 台北19:00（cron 0 11 * * *） → line-remind repo 的 remind.yml（只有週二才發）
 *   - 每天 台北06:00（cron 0 22 * * *） → line-remind repo 的 daily_plan.yml（只有週一~週五才發）
 *
 * 需要的環境變數（Cloudflare Worker 的 Settings → Variables and Secrets）：
 *   LINE_CHANNEL_SECRET   LINE Developers → Basic settings → Channel secret（驗證簽章）
 *   LINE_TOKEN            Messaging API 的 channel access token（回覆私訊用）
 *   GH_PAT                GitHub fine-grained PAT，只授權 hopekids-bot repo 的
 *                         Actions: Read and write
 *   GH_PAT_LINE_REMIND    另一組 fine-grained PAT，只授權 line-remind repo 的
 *                         Actions: Read and write（獨立金鑰，權限互不影響）
 *   ALLOWED_USER_ID       允許觸發的 LINE userId（第一次私訊 bot 會回你自己的 id）
 */

const KEYWORD = "本週服事夥伴";
const REPO = "JoeYoung6406/hopekids-bot";
const WORKFLOW = "weekly.yml";
const LINE_REMIND_REPO = "JoeYoung6406/line-remind";

async function verifySignature(secret, bodyText, signature) {
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign(
    "HMAC", key, new TextEncoder().encode(bodyText));
  const expected = btoa(String.fromCharCode(...new Uint8Array(mac)));
  return expected === signature;
}

async function dispatchWorkflow(env, workflow = WORKFLOW, repo = REPO, token = env.GH_PAT) {
  const resp = await fetch(
    `https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/vnd.github+json",
        "User-Agent": "hopekids-line-webhook",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({ ref: "main" }),
    });
  return resp.status === 204;
}

async function reply(env, replyToken, text) {
  await fetch("https://api.line.me/v2/bot/message/reply", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${env.LINE_TOKEN}`,
    },
    body: JSON.stringify({ replyToken, messages: [{ type: "text", text }] }),
  });
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Hope Kids Bot webhook OK");
    }

    const bodyText = await request.text();
    const signature = request.headers.get("x-line-signature") || "";
    if (!(await verifySignature(env.LINE_CHANNEL_SECRET, bodyText, signature))) {
      return new Response("bad signature", { status: 403 });
    }

    const body = JSON.parse(bodyText);
    for (const ev of body.events || []) {
      if (ev.type !== "message" || ev.message?.type !== "text") continue;
      if (ev.source?.type !== "user") continue; // 只接受私訊，群組訊息一律忽略
      if (ev.message.text.trim() !== KEYWORD) continue;

      const userId = ev.source.userId;
      if (env.ALLOWED_USER_ID && userId === env.ALLOWED_USER_ID) {
        const ok = await dispatchWorkflow(env);
        await reply(env, ev.replyToken, ok
          ? "收到！本週服事卡片馬上發到群組（約 1 分鐘內）～"
          : "觸發失敗，請檢查 Worker 的 GH_PAT 設定。");
      } else {
        await reply(env, ev.replyToken,
          `你沒有觸發權限。\n你的 userId 是：\n${userId}\n\n（第一次設定：把這串填入 Worker 的 ALLOWED_USER_ID 變數）`);
      }
    }
    return new Response("ok");
  },

  // Cloudflare Cron Triggers（在 Worker → Settings → Triggers 底下加，可以掛多組）：
  //   0 2 * * *   每天 台北10:00 → hopekids-bot（依星期/日期判斷要不要發）
  //   0 11 * * *  每天 台北19:00 → line-remind 的 remind.yml（只有週二才發，週幾判斷交給程式碼）
  //   0 22 * * *  每天 台北06:00 → line-remind 的 daily_plan.yml（只有週一~週五才發，同樣交給程式碼）
  //
  // 這兩組都刻意用「每天觸發」而不是在 cron 字串裡指定星期幾：
  // Cloudflare 的 Cron Trigger 介面星期欄位編號跟一般 Linux cron 不同（且對範圍/清單
  // 語法會驗證失敗），與其去猜它的規則，不如每天都觸發、星期幾要不要發交給下面的
  // JS 判斷（用標準 JS Date.getUTCDay()，0=日 1=一 2=二…完全掌握在自己手上）。
  async scheduled(event, env, ctx) {
    if (event.cron === "0 11 * * *") {
      // 台北 19:00（只有週二才發）：小組聚會提醒，用獨立的 line-remind 專屬 PAT
      const taipeiNow = new Date(Date.now() + 8 * 3600 * 1000);
      const dow = taipeiNow.getUTCDay(); // 0=日 1=一 2=二 … 6=六
      if (dow === 2) {
        ctx.waitUntil(dispatchWorkflow(env, "remind.yml", LINE_REMIND_REPO, env.GH_PAT_LINE_REMIND));
      }
      return;
    }

    if (event.cron === "0 22 * * *") {
      // 台北 06:00（只有週一~週五才發，週末跳過）：每日計畫發送，用 line-remind 專屬 PAT
      const taipeiNow = new Date(Date.now() + 8 * 3600 * 1000);
      const dow = taipeiNow.getUTCDay(); // 0=日 1=一 … 6=六（此時已是台北當天早上的星期幾）
      if (dow >= 1 && dow <= 5) {
        ctx.waitUntil(dispatchWorkflow(env, "daily_plan.yml", LINE_REMIND_REPO, env.GH_PAT_LINE_REMIND));
      }
      return;
    }

    // 其餘（0 2 * * *，每天 台北10:00）沿用原本依星期/日期判斷的邏輯
    const taipei = new Date(Date.now() + 8 * 3600 * 1000);
    const dow = taipei.getUTCDay();          // 0=日 1=一 2=二 3=三 …
    const month = taipei.getUTCMonth() + 1;  // 1-12
    const date = taipei.getUTCDate();

    // 每週三 10:00：本週服事夥伴
    if (dow === 3) {
      ctx.waitUntil(dispatchWorkflow(env, "weekly.yml"));
    }

    // 單數月、第三個主日的隔天（週一）10:00：無法參與服事日期回覆表單
    if (month % 2 === 1 && dow === 1 && date === mondayAfterThirdSunday(taipei)) {
      ctx.waitUntil(dispatchWorkflow(env, "unavailable_form.yml"));
    }
  },
};

// 回傳當月「第三個主日的隔天週一」是幾號。
function mondayAfterThirdSunday(taipei) {
  const y = taipei.getUTCFullYear();
  const m = taipei.getUTCMonth();
  const firstDow = new Date(Date.UTC(y, m, 1)).getUTCDay(); // 該月 1 號星期幾
  const firstSunday = 1 + ((7 - firstDow) % 7);             // 第一個主日日期
  return firstSunday + 14 + 1;                              // 第三主日 +1 天
}
