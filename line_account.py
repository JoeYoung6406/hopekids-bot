# -*- coding: utf-8 -*-
"""共用：決定這次用哪一隻 LINE 官方帳號推播，並送出 push。

平常一律用 A 帳號（LINE_TOKEN / LINE_GROUP_ID）。
當月（台北時間）列在 account_b_months.txt 的話改用 B 帳號
（LINE_TOKEN_B / LINE_GROUP_ID_B；沒設 LINE_GROUP_ID_B 就沿用 LINE_GROUP_ID）。

LINE 一個群組同時只能有一隻官方帳號，所以不能兩隻同時輪流發；
換月份時要手動在群組裡把 bot 換掉（詳見 README）。
"""
import datetime as dt
import os
import sys
from pathlib import Path

import requests

MONTHS_FILE = Path(__file__).with_name("account_b_months.txt")
TAIPEI = dt.timezone(dt.timedelta(hours=8))


def this_month():
    return dt.datetime.now(TAIPEI).strftime("%Y-%m")


def active_account(month=None):
    """這個月要用的帳號："A" 或 "B"。"""
    month = month or this_month()
    if MONTHS_FILE.exists():
        for line in MONTHS_FILE.read_text(encoding="utf-8").splitlines():
            if line.partition("#")[0].strip() == month:
                return "B"
    return "A"


def credentials():
    """回傳 (帳號, token, group_id)。這個月該用 B 卻沒設 token 就直接失敗，不偷偷退回 A。"""
    account = active_account()
    if account == "B":
        token = os.environ.get("LINE_TOKEN_B")
        if not token:
            sys.exit(f"{this_month()} 列在 account_b_months.txt 要用 B 帳號，"
                     "但沒有 LINE_TOKEN_B（請先設定 GitHub secret）。")
        group_id = os.environ.get("LINE_GROUP_ID_B") or os.environ["LINE_GROUP_ID"]
    else:
        token, group_id = os.environ["LINE_TOKEN"], os.environ["LINE_GROUP_ID"]
    return account, token, group_id


def push(message):
    account, token, group_id = credentials()
    if os.environ.get("LINE_TEST_BROADCAST"):
        # 測試用：發給這隻帳號的所有好友，不發到群組（好友只有自己時就等於私訊自己）
        print(f"[測試] 使用 {account} 帳號 broadcast 給所有好友（{this_month()}）")
        return requests.post(
            "https://api.line.me/v2/bot/message/broadcast",
            headers={"Authorization": f"Bearer {token}"},
            json={"messages": [message]},
            timeout=30,
        )
    print(f"使用 {account} 帳號推播（{this_month()}）")
    return requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Authorization": f"Bearer {token}"},
        json={"to": group_id, "messages": [message]},
        timeout=30,
    )
