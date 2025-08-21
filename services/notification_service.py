import json
import os
import logging
from datetime import datetime
import pytz
from line_service import push_message_to_user
from database.db import get_user_reply, has_replied, reset_replies_db
from config import config
from utils.date_utils import get_friday

# 設定 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 設定台灣時區
tz = pytz.timezone(config.TIMEZONE)

def load_user_config():
    """載入使用者配置"""
    try:
        if not os.path.exists(config.USERS_CONFIG_PATH):
            logger.warning(f"找不到 {config.USERS_CONFIG_PATH}，請建立此檔案")
            return {"users": []}
        with open(config.USERS_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("配置載入錯誤: %s", e)
        return {"users": []}

def send_ask_notification(user):
    """發送詢問通知"""
    friday_str = get_friday()
    today = datetime.now(tz).strftime("%A").lower()

    # 檢查使用者是否已回覆
    if has_replied(user["user_id"]):
        logger.info("%s 已回覆，不發送詢問通知", user["name"])
        return

    if today == "tuesday":
        message = (
            f"嗨嗨～再提醒一次！\n禮拜五({friday_str})晚上{config.BADMINTON_LOCATION}，{config.BADMINTON_TIME}。\n"
            "目前還有些人沒回覆會不會來，幫個忙回覆一下 🙏\n"
            "人數掌握一下比較好排場次～\n\n"
            "請回覆「要」或「不要」喔！"
        )
    elif today == "friday":
        message = (
            f"後天就要打球啦～\n禮拜五({friday_str} {config.BADMINTON_TIME}) {config.BADMINTON_LOCATION}！\n"
            "還沒回覆的，今天務必講一下要不要來，\n"
            "我們要安排場次、人數，不能再靠猜的了～\n"
            "再不說，真的會派人面對面來問你喔（不是開玩笑）👀\n\n"
            "請回覆「要」或「不要」喔！"
        )
    else:
        message = (
            f"嗨各位~\n這週五({friday_str} {config.BADMINTON_TIME})\n"
            f"我們照常在{config.BADMINTON_LOCATION}打球，\n回復一下你會不會來吧，讓我們好抓人數喔~\n\n"
            "請回覆「要」或「不要」喔！"
        )

    push_message_to_user(user["user_id"], message)
    logger.info("已向 %s 發送詢問通知", user["name"])

def send_summary_notification(user):
    """發送統計摘要通知"""
    try:
        yes_list, no_list, no_reply_list = get_user_reply()
        friday_str = get_friday()

        summary = f"出席統計（{friday_str}）\n"
        summary += f"✅ 要打球（{len(yes_list)}人）:\n"
        summary += "\n".join(f"- {name}" for name in yes_list) or "（無）"
        summary += f"\n\n❌ 不打球（{len(no_list)}人）:\n"
        summary += "\n".join(f"- {name}" for name in no_list) or "（無）"
        summary += f"\n\n😡 未回應（{len(no_reply_list)}人）:\n"
        summary += "\n".join(f"- {name}" for name in no_reply_list) or "（無）"

        push_message_to_user(user["user_id"], summary)
        logger.info("已向 %s 發送統計摘要", user["name"])
    except Exception as e:
        logger.error("摘要發送錯誤: %s", e)

def reset_replies_with_log():
    """重置回覆狀態（帶日誌）"""
    try:
        reset_replies_db()
        logger.info("已重置所有人的回覆狀態（reset_replies）")
    except Exception as e:
        logger.error("重置回覆狀態時發生錯誤: %s", e)
