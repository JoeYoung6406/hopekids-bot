# -*- coding: utf-8 -*-
"""推播「無法參與服事日期回覆表單」提醒卡片到 LINE 群組。

發送時機（由 Cloudflare Worker 判斷）：單數月、第三個主日的隔天週一、早上 10:00。
調查對象＝發送月往後推的兩個月（例：7 月發 → 調查 9、10 月；9 月發 → 11、12 月）。
本機測試：DRY_RUN=1 python push_unavailable_form.py
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

FORM_URL = "https://docs.google.com/forms/d/1CtC82qZ_8a-tNdKoJiAuqaDJUa5jrwrFpcXaqZa4GOQ/viewform"

SUN = "#ffc33b"
SUN_DEEP = "#f2a900"
INK = "#4a3b22"
BG_SOFT = "#fffdf6"


def surveyed_months(month):
    """回傳調查的兩個月（發送月 +2、+3，跨年自動迴繞）。"""
    return (month + 1) % 12 + 1, (month + 2) % 12 + 1


def build_flex():
    taipei = datetime.now(timezone.utc) + timedelta(hours=8)
    m1, m2 = surveyed_months(taipei.month)
    title = f"{m1}、{m2}月 無法參與服事日期回覆表單"

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": SUN, "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "HOPE KIDS 台中分部", "size": "xs",
                 "weight": "bold", "color": INK},
                {"type": "text", "text": title, "size": "lg", "weight": "bold",
                 "color": INK, "wrap": True, "margin": "sm"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "backgroundColor": BG_SOFT, "paddingAll": "20px", "spacing": "md",
            "contents": [
                {"type": "text",
                 "text": "請各位服事夥伴抽空填寫\n以利同工安排服事表",
                 "size": "sm", "color": INK, "wrap": True, "align": "center"},
                {"type": "text", "text": "上帝紀念你 / 妳的擺上 ～",
                 "size": "sm", "color": SUN_DEEP, "weight": "bold",
                 "wrap": True, "align": "center"},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": [{
                "type": "button", "style": "primary", "color": INK, "height": "sm",
                "action": {"type": "uri", "label": "填寫回覆表單", "uri": FORM_URL},
            }],
        },
    }
    return {"type": "flex", "altText": title, "contents": bubble}


def main():
    message = build_flex()
    if os.environ.get("DRY_RUN"):
        print(json.dumps(message, ensure_ascii=False, indent=2))
        return
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Authorization": f"Bearer {os.environ['LINE_TOKEN']}"},
        json={"to": os.environ["LINE_GROUP_ID"], "messages": [message]},
        timeout=30,
    )
    if resp.status_code == 200:
        print("[成功] 已推播 無法參與服事日期回覆表單")
    else:
        print(f"[失敗] {resp.status_code}：{resp.text}")
        sys.exit(1)


if __name__ == "__main__":
    main()
