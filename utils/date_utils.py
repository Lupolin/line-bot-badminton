from datetime import datetime, timedelta
import pytz
from config import config

# 設定台灣時區
tz = pytz.timezone(config.TIMEZONE)

def get_friday():
    """取得下一個週五的日期"""
    today = datetime.now(tz)
    days_ahead = (4 - today.weekday() + 7) % 7  # 4 = Friday
    if days_ahead == 0:
        days_ahead = 7  # 今天就是週五的話，下一個週五是 7 天後
    next_friday = today + timedelta(days=days_ahead)
    return next_friday.strftime("%m/%d")  # e.g. 06/28
