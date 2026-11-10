# -*- coding: utf-8 -*-
"""排定日期的活動通知卡（例如活動出席回覆表單）。

跟每週三 10:00 的服事表放在「同一則」推播裡一起發：LINE 一次 push 最多 5 張卡片，
算一則訊息，不會多扣群組人數的額度。只有當天（台北時間）列在 NOTICES 裡才會附上。
本機預覽：python notices.py 2026-11-11
"""
import datetime as dt
import json
import sys

TAIPEI = dt.timezone(dt.timedelta(hours=8))

SUN = "#ffc33b"
SUN_DEEP = "#f2a900"
INK = "#4a3b22"
TEAL = "#2bb3a3"
CORAL = "#ff7a59"
BG_SOFT = "#fffdf6"
MUTED = "#a08d6a"


def slot_row(badge, color, title, detail):
    """左邊彩色時段標籤，右邊兩行說明。"""
    return {
        "type": "box", "layout": "horizontal", "alignItems": "center", "spacing": "md",
        "contents": [
            {
                "type": "box", "layout": "vertical", "backgroundColor": color,
                "cornerRadius": "6px", "paddingAll": "4px", "width": "52px",
                "contents": [{"type": "text", "text": badge, "size": "xs", "weight": "bold",
                              "color": "#ffffff", "align": "center"}],
            },
            {
                "type": "box", "layout": "vertical", "flex": 1,
                "contents": [
                    {"type": "text", "text": title, "size": "sm", "weight": "bold",
                     "color": INK, "wrap": True},
                    {"type": "text", "text": detail, "size": "xs", "color": MUTED, "wrap": True},
                ],
            },
        ],
    }


def form_card(title, slots, message, note, button_label, url):
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
            "backgroundColor": BG_SOFT, "paddingAll": "16px", "spacing": "md",
            "contents": [slot_row(*s) for s in slots] + [
                {"type": "separator", "margin": "md", "color": "#f3e6c8"},
                {"type": "text", "text": message, "size": "sm", "color": INK,
                 "wrap": True, "margin": "md"},
                {"type": "text", "text": note, "size": "xs", "color": SUN_DEEP,
                 "weight": "bold", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": [{
                "type": "button", "style": "primary", "color": INK, "height": "sm",
                "action": {"type": "uri", "label": button_label, "uri": url},
            }],
        },
    }
    return {"type": "flex", "altText": title, "contents": bubble}


# 日期（台北 YYYY-MM-DD）→ 當天要附上的卡片；過期的留著不影響
NOTICES = {
    "2026-11-11": [form_card(
        title="11/15（日）備課日＆團隊聚集",
        slots=[
            ("下午", TEAL, "13:30–16:00 備課日", "Kids Central"),
            ("晚上", CORAL, "18:00–20:00 團隊聚集", "Joe 的家｜一家帶 1–2 道菜（3–4 人份）"),
        ],
        message="請大家點下方按鈕回覆備課日出席，晚上團隊聚集也一起填人數 🙌",
        note="已經填過備課日的夥伴，請再填一次補上聚集人數（會更新原本的回覆）",
        button_label="填寫出席回覆",
        url="https://joeyoung6406.github.io/hopekids-tc/events/20261115-prep/",
    )],
}


def today_messages(today=None):
    today = today or dt.datetime.now(TAIPEI).date().isoformat()
    return NOTICES.get(today, [])


if __name__ == "__main__":
    msgs = today_messages(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(msgs, ensure_ascii=False, indent=2) if msgs else "這天沒有活動通知卡")
