# -*- coding: utf-8 -*-
"""Hope Kids Bot — 每週把「當週服事表」推播到 LINE 群組（Flex 卡片）。

資料來源：Google 試算表「當週服事表」分頁（公開連結讀取）。
執行方式：GitHub Actions 排程呼叫，或本機 DRY_RUN=1 python push_weekly.py 測試。
"""
import csv
import io
import json
import os
import re
import sys

import requests

SHEET_ID = "1S08InCXZ9Al7I_L1BRRgDmH4w4NQaFTKERJ9-6yVZsQ"
WEEKLY_GID = "1159891743"  # 當週服事表分頁
SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/gviz/tq?tqx=out:csv&gid={WEEKLY_GID}"
)
SHEET_VIEW_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/edit?gid={WEEKLY_GID}#gid={WEEKLY_GID}"
)

# 要顯示在卡片上的崗位（依這個順序排列）
ROLES = [
    "敬拜", "禱告", "奉獻", "投影", "破冰",
    "大班故事", "小班故事", "大班勞作", "小班勞作",
]
# 崗位標籤配色（Hope Kids 品牌色循環）
BADGE_COLORS = ["#f2a900", "#ff7a59", "#2bb3a3"]

INK = "#4a3b22"
SUN = "#ffc33b"
BG_SOFT = "#fffdf6"


def fetch_rows():
    resp = requests.get(SHEET_CSV_URL, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return list(csv.reader(io.StringIO(resp.text)))


def parse_schedule(rows):
    """回傳 (日期字串, {崗位: 名字}, 值日生, Rally 說明)。"""
    date_str = None
    roles = {}
    duty = None
    rally = None

    for row in rows:
        for cell in row:
            cell = (cell or "").strip()
            if not cell:
                continue
            # 日期：2026/07/19
            m = re.search(r"日期[：:]\s*(\d{4}/\d{1,2}/\d{1,2})", cell)
            if m and date_str is None:
                date_str = m.group(1)
            # 崗位：名字（同一格可能有多行）
            for line in cell.splitlines():
                lm = re.match(r"\s*([^：:]{1,8})[：:]\s*(.+)", line.strip())
                if lm:
                    role, name = lm.group(1).strip(), lm.group(2).strip()
                    if role in ROLES and role not in roles and name:
                        roles[role] = name
        # 值日生、Rally 從「作業流程」欄位找
        cells = [(c or "").strip() for c in row]
        for i, cell in enumerate(cells):
            if "值日生" in cell and duty is None:
                # 名單在「負責人員」欄（該列最後一個非空欄位）
                non_empty = [c for c in cells if c]
                if non_empty and non_empty[-1] != cell:
                    duty = non_empty[-1]
            if cell == "Rally" and rally is None:
                time_part = next((c for c in cells[:i] if re.match(r"\d{1,2}:\d{2}", c)), "")
                note_part = next((c for c in cells[i + 1:] if c), "")
                rally = " ".join(x for x in [time_part, note_part] if x)

    return date_str, roles, duty, rally


def weekday_zh(date_str):
    from datetime import datetime
    try:
        d = datetime.strptime(date_str, "%Y/%m/%d")
        return "（週" + "一二三四五六日"[d.weekday()] + "）"
    except ValueError:
        return ""


def role_row(label, name, color):
    return {
        "type": "box",
        "layout": "horizontal",
        "alignItems": "center",
        "spacing": "md",
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": color,
                "cornerRadius": "6px",
                "paddingAll": "4px",
                "width": "88px",
                "contents": [{
                    "type": "text",
                    "text": label,
                    "size": "xs",
                    "weight": "bold",
                    "color": "#ffffff",
                    "align": "center",
                }],
            },
            {
                "type": "text",
                "text": name or "—",
                "size": "sm",
                "color": INK,
                "wrap": True,
                "flex": 1,
            },
        ],
    }


def build_flex(date_str, roles, duty, rally):
    day = f"{date_str} {weekday_zh(date_str)}" if date_str else "本週主日"

    body_rows = []
    for i, role in enumerate(ROLES):
        body_rows.append(role_row(role, roles.get(role), BADGE_COLORS[i % len(BADGE_COLORS)]))
    if duty:
        body_rows.append({"type": "separator", "margin": "md", "color": "#f3e6c8"})
        body_rows.append(role_row("當天值日生", duty, INK))

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": SUN,
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "HOPE KIDS 台中分部", "size": "xs",
                 "weight": "bold", "color": INK},
                {"type": "text", "text": "本週服事夥伴", "size": "xl",
                 "weight": "bold", "color": INK, "margin": "xs"},
                {"type": "text", "text": day, "size": "sm", "color": INK, "margin": "xs"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BG_SOFT,
            "spacing": "sm",
            "paddingAll": "16px",
            "contents": (
                ([{"type": "text", "text": f"📍 Rally {rally}", "size": "xs",
                   "color": "#a08d6a", "wrap": True, "margin": "none"}] if rally else [])
                + body_rows
            ),
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": INK,
                    "height": "sm",
                    "action": {"type": "uri", "label": "查看完整服事表",
                               "uri": SHEET_VIEW_URL},
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {"type": "uri", "label": "服事夥伴專區",
                               "uri": "https://joeyoung6406.github.io/hopekids-tc/"},
                },
            ],
        },
    }

    return {
        "type": "flex",
        "altText": f"Hope Kids 本週服事夥伴 {date_str or ''}".strip(),
        "contents": bubble,
    }


def push(message):
    token = os.environ["LINE_TOKEN"]
    group_id = os.environ["LINE_GROUP_ID"]
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Authorization": f"Bearer {token}"},
        json={"to": group_id, "messages": [message]},
        timeout=30,
    )
    return resp


def main():
    rows = fetch_rows()
    date_str, roles, duty, rally = parse_schedule(rows)

    if not date_str and not roles:
        print("試算表沒有可用的日期與崗位資料，跳過本次推播。")
        return

    message = build_flex(date_str, roles, duty, rally)

    if os.environ.get("DRY_RUN"):
        print(json.dumps(message, ensure_ascii=False, indent=2))
        print(f"\n[DRY RUN] 解析結果：日期={date_str} 崗位={roles} 值日生={duty} Rally={rally}")
        return

    resp = push(message)
    if resp.status_code == 200:
        print(f"[成功] 已推播 {date_str} 服事表")
    else:
        print(f"[失敗] {resp.status_code}：{resp.text}")
        sys.exit(1)


if __name__ == "__main__":
    main()
