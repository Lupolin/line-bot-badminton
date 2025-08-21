# db_mysql.py
import os
import json
import logging
from datetime import datetime
import pymysql
from config import config

# 設定 logger
logger = logging.getLogger(__name__)

# 使用配置管理系統
DB_HOST = config.DB_HOST
DB_PORT = config.DB_PORT
DB_USER = config.DB_USER
DB_PASSWORD = config.DB_PASSWORD
DB_NAME = config.DB_NAME
DB_SSL_CA = config.DB_SSL_CA  # 可為空

TABLE = config.DB_TABLE

def _conn():
    kwargs = dict(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
        connect_timeout=10,
        autocommit=False,
    )
    if DB_SSL_CA:
        kwargs["ssl"] = {"ca": DB_SSL_CA}
    return pymysql.connect(**kwargs)

def init_db():
    """若你想用程式側建立表，可呼叫這個。通常建議用上面的 SQL 建表即可。"""
    ddl = f"""
    CREATE TABLE IF NOT EXISTS `{TABLE}` (
      `id`           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      `user_id`      VARCHAR(64),
      `user_name`    VARCHAR(128),
      `reply_text`   VARCHAR(255),
      `has_replied`  TINYINT(1) NOT NULL DEFAULT 0,
      `timestamp`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,
      KEY `idx_user_ts` (`user_id`,`timestamp`),
      KEY `idx_ts_date` ((date(`timestamp`)))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    conn = _conn()
    try:
        with conn.cursor() as c:
            c.execute(ddl)
        conn.commit()
    finally:
        conn.close()

def insert_reply(user_id, user_name, reply_text):
    """同人：若有則更新；沒有則新增。不區分日期。"""
    conn = _conn()
    try:
        with conn.cursor() as c:
            # 查使用者是否已存在（不分日期）
            c.execute(
                f"""
                SELECT id FROM `{TABLE}`
                WHERE user_id=%s
                LIMIT 1
                """,
                (user_id,),
            )
            row = c.fetchone()

            if row:
                # 使用者已存在，更新回覆
                c.execute(
                    f"""
                    UPDATE `{TABLE}`
                    SET reply_text=%s, user_name=%s, has_replied=1, `timestamp`=NOW()
                    WHERE user_id=%s
                    """,
                    (reply_text, user_name, user_id),
                )
            else:
                # 使用者不存在，新增記錄
                c.execute(
                    f"""
                    INSERT INTO `{TABLE}` (user_id, user_name, reply_text, has_replied, `timestamp`)
                    VALUES (%s, %s, %s, 1, NOW())
                    """,
                    (user_id, user_name, reply_text),
                )
        conn.commit()
    finally:
        conn.close()

def has_replied(user_id):
    """檢查使用者是否有回覆（不分時間，只看 reply_text 是否有值）"""
    conn = _conn()
    try:
        with conn.cursor() as c:
            c.execute(
                f"""
                SELECT COUNT(*) FROM `{TABLE}`
                WHERE user_id=%s AND reply_text IS NOT NULL AND reply_text != ''
                """,
                (user_id,),
            )
            (count,) = c.fetchone()
            return count > 0
    finally:
        conn.close()

def update_reply(user_id, reply_text):
    """更新使用者的回覆（不分時間，僅當內容不同時才更新）"""
    conn = _conn()
    try:
        with conn.cursor() as c:
            c.execute(
                f"""
                SELECT reply_text FROM `{TABLE}`
                WHERE user_id=%s
                LIMIT 1
                """,
                (user_id,),
            )
            row = c.fetchone()
            if row is None or row[0] == reply_text:
                return False

            c.execute(
                f"""
                UPDATE `{TABLE}`
                SET reply_text=%s, has_replied=1, `timestamp`=NOW()
                WHERE user_id=%s
                """,
                (reply_text, user_id),
            )
        conn.commit()
        return True
    finally:
        conn.close()

def get_user_reply():
    """
    回傳: (yes_list, no_list, no_reply_list)
    - yes_list：reply_text 為"要"的使用者
    - no_list：reply_text 為"不要"的使用者  
    - no_reply_list：reply_text 為 NULL 或空的使用者
    """
    conn = _conn()
    try:
        with conn.cursor() as c:
            # 查詢所有使用者的當前回覆狀態（不分時間）
            c.execute(f"""
                SELECT user_id, user_name, reply_text
                FROM `{TABLE}`
                WHERE reply_text IS NOT NULL AND reply_text != ''
            """)
            replied_users = c.fetchall()
            
            # 查詢所有使用者（不分時間）
            c.execute(f"SELECT DISTINCT user_id, user_name FROM `{TABLE}`")
            all_users = c.fetchall()
    finally:
        conn.close()

    # 分類回覆狀態
    yes_list = [r[1] for r in replied_users if r[2] in config.YES_KEYWORDS]
    no_list = [r[1] for r in replied_users if r[2] in config.NO_KEYWORDS]
    
    # 找出沒有回覆的使用者（reply_text 為 NULL 或空）
    replied_user_ids = {r[0] for r in replied_users}
    no_reply_list = [name for uid, name in all_users if uid not in replied_user_ids]
    
    return yes_list, no_list, no_reply_list

def reset_replies_db():
    """將所有人的 reply_text 變為空，has_replied 設為 0"""
    conn = _conn()
    try:
        with conn.cursor() as c:
            c.execute(
                f"""
                UPDATE `{TABLE}`
                SET reply_text = '', has_replied = 0
                """
            )
        conn.commit()
        logger.info("已重置所有使用者的回覆狀態")
    except Exception as e:
        logger.error(f"重置回覆狀態時發生錯誤: {e}")
        raise
    finally:
        conn.close()

# 你原本的輔助：讀 config 取名字（保持不變）
def get_name_from_config(user_id):
    config_path = config.USERS_CONFIG_PATH
    if not os.path.exists(config_path):
        return "未知使用者"
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
            for user in data.get("users", []):
                if user.get("user_id") == user_id:
                    return user.get("name", "未知使用者")
    except Exception:
        return "未知使用者"
    return "未知使用者"
