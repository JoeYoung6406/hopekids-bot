# -*- coding: utf-8 -*-
"""共用：判斷今天（台北時間）是否列在 skip_dates.txt，是的話就不推播。

推播腳本會直接正常結束（exit 0），所以 GitHub Actions 那次執行算成功，
watchdog 也就不會誤判成漏發而補發。
"""
import datetime as dt
from pathlib import Path

SKIP_FILE = Path(__file__).with_name("skip_dates.txt")
TAIPEI = dt.timezone(dt.timedelta(hours=8))


def today_taipei():
    return dt.datetime.now(TAIPEI).date().isoformat()


def skip_reason(today=None):
    """今天要跳過就回傳原因（可能是空字串），否則回傳 None。"""
    today = today or today_taipei()
    if not SKIP_FILE.exists():
        return None
    for line in SKIP_FILE.read_text(encoding="utf-8").splitlines():
        date, _, reason = line.partition("#")
        if date.strip() == today:
            return reason.strip()
    return None


def skipped():
    """要跳過就印出訊息並回傳 True。"""
    reason = skip_reason()
    if reason is None:
        return False
    print(f"今天（台北 {today_taipei()}）列在 skip_dates.txt，跳過本次推播。{reason}")
    return True
