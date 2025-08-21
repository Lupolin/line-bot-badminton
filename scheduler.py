# scheduler_setup.py  （你的原檔名照舊也可以）
from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo
from datetime import datetime
import logging

from services.notification_service import (
    load_user_config,
    send_ask_notification,
    send_summary_notification,
    reset_replies_with_log,
)
from config import config

# ✅ logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ✅ 建立排程器（帶時區）
scheduler = BackgroundScheduler(timezone=config.TIMEZONE)

# 防止重複啟動的標記
_scheduler_started = False

def _cron_day(d: str) -> str:
    """把 full name 轉 APScheduler 縮寫 (tuesday -> tue)"""
    d = (d or "").strip().lower()
    mapping = {
        "monday":"mon","tuesday":"tue","wednesday":"wed",
        "thursday":"thu","friday":"fri","saturday":"sat","sunday":"sun",
    }
    return mapping.get(d, d[:3])

def schedule_from_config():
    """依 users 的 notification_times 直接建立 cron 任務"""
    cfg = load_user_config()
    tz = ZoneInfo(config.TIMEZONE)

    # 先移除舊的 user-* 任務（避免重複）
    for job in list(scheduler.get_jobs()):
        if job.id and job.id.startswith("user-"):
            scheduler.remove_job(job.id)
            logger.info("移除舊任務: %s", job.id)

    for user in cfg.get("users", []):
        uid = user["user_id"]
        uname = user.get("name", uid)

        for i, nt in enumerate(user.get("notification_times", [])):
            day  = _cron_day(nt["day"])
            hour = int(nt["hour"])
            minute = int(nt["minute"])
            typ  = nt.get("type", "ask").lower()

            func = send_summary_notification if typ == "summary" else send_ask_notification
            job_id = f"user-{uid}-{i}-{typ}"

            scheduler.add_job(
                func=func,
                trigger="cron",
                day_of_week=day,
                hour=hour,
                minute=minute,
                args=[user],                  # 把 user 當參數傳進通知函式
                id=job_id,
                replace_existing=True,
                timezone=tz
            )
            logger.info("已排程 → %s：%s %02d:%02d (%s)", uname, day, hour, minute, typ)

def start_scheduler():
    global _scheduler_started
    
    # 防止重複啟動
    if _scheduler_started:
        logger.warning("排程器已經啟動，跳過重複啟動")
        return
    
    # 檢查排程器狀態
    if scheduler.running:
        logger.warning("排程器正在運行中，跳過重複啟動")
        return
    
    try:
        # ✅ 用 cron 固定時間觸發，不再每分鐘輪詢
        schedule_from_config()

        # 保留每週重置任務
        scheduler.add_job(
            reset_replies_with_log,
            'cron',
            day_of_week=config.RESET_REPLIES_DAY,
            hour=21,
            minute=0,
            id="weekly-reset",
            replace_existing=True
        )

        scheduler.start()
        _scheduler_started = True
        logger.info("排程器已啟動（時區：%s）。已改為固定時間觸發。", config.TIMEZONE)
        
        # 顯示當前所有任務
        jobs = scheduler.get_jobs()
        logger.info("當前排程任務數量: %d", len(jobs))
        for job in jobs:
            logger.info("任務: %s - %s", job.id, job.trigger)
            
    except Exception as e:
        logger.error("啟動排程器時發生錯誤: %s", e)
        _scheduler_started = False