from datetime import datetime, timedelta
import json
import os
import pytz
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from line_service import push_message_to_user
from db import get_today_stats
import sqlite3

# ✅ 設定 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ✅ 設定台灣時區
tz = pytz.timezone("Asia/Taipei")

def get_friday():
    today = datetime.now(tz)
    days_ahead = (4 - today.weekday() + 7) % 7  # 4 = Friday
    if days_ahead == 0:
        days_ahead = 7  # 今天就是週五的話，下一個週五是 7 天後
    next_friday = today + timedelta(days=days_ahead)
    return next_friday.strftime("%m/%d")  # e.g. 06/28

def load_user_config():
    try:
        if not os.path.exists("users_config.json"):
            logger.warning("找不到 users_config.json，請建立此檔案")
            return {"users": []}
        with open("users_config.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("配置載入錯誤: %s", e)
        return {"users": []}

def send_ask_notification(user):
    friday_str = get_friday()
    today = datetime.now(tz).strftime("%A").lower()

    # 檢查使用者是否已回覆
    # 從 reply.db 讀取該 user 是否已回覆
    conn = sqlite3.connect('reply.db')
    c = conn.cursor()
    c.execute("SELECT has_replied FROM replies WHERE user_id = ?", (user["user_id"],))
    row = c.fetchone()
    conn.close()
    if row and str(row[0]).lower() in ("1", "true"):
        logger.info("%s 已回覆，不發送詢問通知", user["name"])
        return

    if today == "thursday":
        message = (
            f"嗨嗨～再提醒一次！\n禮拜五({friday_str})晚上信義國小羽球場，6點到8點。\n"
            "目前還有些人沒回覆會不會來，幫個忙回覆一下 🙏\n"
            "人數掌握一下比較好排場次～\n\n"
            "請回覆「要」或「不要」喔！"
        )
    elif today == "friday":
        message = (
            f"後天就要打球啦～\n禮拜五({friday_str} 18:00–20:00) 信義國小！\n"
            "還沒回覆的，今天務必講一下要不要來，\n"
            "我們要安排場次、人數，不能再靠猜的了～\n"
            "再不說，真的會派人面對面來問你喔（不是開玩笑）👀\n\n"
            "請回覆「要」或「不要」喔！"
        )
    else:
        message = (
            f"嗨各位~\n這週五({friday_str} 18:00-20:00)\n"
            "我們照常在信義國小打球，\n回復一下你會不會來吧，讓我們好抓人數喔~\n\n"
            "請回覆「要」或「不要」喔！"
        )

    push_message_to_user(user["user_id"], message)
    logger.info("已向 %s 發送詢問通知", user["name"])


def send_summary_notification(user):
    try:
        yes_list, no_list = get_today_stats("all")
        friday_str = get_friday()

        summary = f"出席統計（{friday_str}）\n"
        summary += f"✅ 要打球（{len(yes_list)}人）:\n"
        summary += "\n".join(f"- {name}" for name in yes_list) or "（無）"
        summary += f"\n\n❌ 不打球（{len(no_list)}人）:\n"
        summary += "\n".join(f"- {name}" for name in no_list) or "（無）"

        push_message_to_user(user["user_id"], summary)
        logger.info("已向 %s 發送統計摘要", user["name"])
    except Exception as e:
        logger.error("摘要發送錯誤: %s", e)

def scheduled_notification():
    config = load_user_config()
    current_time = datetime.now(tz)
    current_day = current_time.strftime("%A").lower()
    current_hour = current_time.hour
    current_minute = current_time.minute

    logger.info("排程檢查: %s %02d:%02d（Asia/Taipei）", current_day, current_hour, current_minute)

    for user in config.get("users", []):
        for notification in user.get("notification_times", []):
            if (
                notification["day"] == current_day and
                notification["hour"] == current_hour and
                notification["minute"] == current_minute
            ):
                if notification["type"] == "ask":
                    send_ask_notification(user)
                elif notification["type"] == "summary":
                    send_summary_notification(user)
                else:
                    send_ask_notification(user)

def reset_replies():
    """每周日晚上九點，將所有人的 reply_text 變為空，has_replied 設為 0"""
    import sqlite3
    conn = sqlite3.connect('reply.db')
    c = conn.cursor()
    c.execute('''
        UPDATE replies
        SET reply_text = '', has_replied = 0
    ''')
    conn.commit()
    conn.close()

# 加入每周日21:00自動執行 reset_replies
def reset_replies_with_log():
    reset_replies()
    logger.info("已重置所有人的回覆狀態（reset_replies）")

# ✅ 建立排程器，但不自動啟動（供 app.py 控制）
scheduler = BackgroundScheduler(timezone=tz)
scheduler.add_job(scheduled_notification, 'cron', minute='*')

scheduler.add_job(reset_replies_with_log, 'cron', day_of_week='sun', hour=21, minute=0)

# ✅ 對外暴露的排程啟動函式
def start_scheduler():
    scheduler.start()
    logger.info("排程器已啟動（start_scheduler）")
