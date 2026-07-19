/**
 * Hope Kids Bot — LINE Webhook (Cloudflare Worker)
 *
 * 私訊 bot「本週服事夥伴」→ 觸發 GitHub Actions 的 weekly.yml
 * → 服事卡片推播到官方群組（約 30~60 秒）。
 *
 * 需要的環境變數（Cloudflare Worker 的 Settings → Variables and Secrets）：
 *   LINE_CHANNEL_SECRET  LINE Developers → Basic settings → Channel secret（驗證簽章）
 *   LINE_TOKEN           Messaging API 的 channel access token（回覆私訊用）
 *   GH_PAT               GitHub fine-grained PAT，只授權 hopekids-bot repo 的
 *                        Actions: Read and write
 *   ALLOWED_USER_ID      允許觸發的 LINE userId（第一次私訊 bot 會回你自己的 id）
 */

const KEYWORD = "本週服事夥伴";
const REPO = "JoeYoung6406/hopekids-bot";
const WORKFLOW = "weekly.yml";

async function verifySignature(secret, bodyText, signature) {
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign(
    "HMAC", key, new TextEncoder().encode(bodyText));
  const expected = btoa(String.fromCharCode(...new Uint8Array(mac)));
  return expected === signature;
}

async function dispatchWorkflow(env) {
  const resp = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GH_PAT}`,
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
};
