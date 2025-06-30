import sqlite3
from datetime import datetime
import json
import os

db_path = "reply.db"

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT,
            user_id TEXT,
            user_name TEXT,
            reply_text TEXT,
            has_replied BOOLEAN DEFAULT 0,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_reply(group_id, user_id, user_name, reply_text):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # 先檢查今天是否已有資料
    c.execute('''
        SELECT id FROM replies
        WHERE group_id = ? AND user_id = ? AND DATE(timestamp) = ?
    ''', (group_id, user_id, today))
    row = c.fetchone()
    if row:
        # 已有資料，執行更新，has_replied設為1
        c.execute('''
            UPDATE replies
            SET reply_text = ?, user_name = ?, has_replied = 1, timestamp = ?
            WHERE id = ?
        ''', (reply_text, user_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), row[0]))
    else:
        # 沒有資料，新增一筆，has_replied設為1
        c.execute('''
            INSERT INTO replies (group_id, user_id, user_name, reply_text, has_replied, timestamp)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (group_id, user_id, user_name, reply_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def has_replied_today(group_id, user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM replies
        WHERE group_id = ? AND user_id = ? AND DATE(timestamp) = ?
    ''', (group_id, user_id, today))
    result = c.fetchone()[0]
    conn.close()
    return result > 0

def update_reply(group_id, user_id, reply_text):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT reply_text FROM replies
        WHERE group_id = ? AND user_id = ? AND DATE(timestamp) = ?
    ''', (group_id, user_id, today))
    row = c.fetchone()
    if row is None:
        conn.close()
        return False
    if row[0] == reply_text:
        conn.close()
        return False

    c.execute('''
        UPDATE replies
        SET reply_text = ?, has_replied = 1, timestamp = ?
        WHERE group_id = ? AND user_id = ? AND DATE(timestamp) = ?
    ''', (reply_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), group_id, user_id, today))
    conn.commit()
    conn.close()
    return True

def get_today_stats(group_id=None):
    """獲取今天的統計，支援特定群組或全局統計，未回覆名單僅統計 reply.db 有出現過的 user"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    if group_id == "all" or group_id is None:
        c.execute('''
            SELECT user_id, user_name, reply_text FROM replies
            WHERE DATE(timestamp) = ?
        ''', (today,))
    else:
        c.execute('''
            SELECT user_id, user_name, reply_text FROM replies
            WHERE group_id = ? AND DATE(timestamp) = ?
        ''', (group_id, today))
    rows = c.fetchall()

    # 取得 reply.db 所有 user_id 對應 name（不分日期）
    c.execute('''SELECT DISTINCT user_id, user_name FROM replies''')
    all_users = c.fetchall()
    conn.close()

    replied_user_ids = set(row[0] for row in rows)
    yes_list = [row[1] for row in rows if row[2] in ["要", "yes", "Yes"]]
    no_list = [row[1] for row in rows if row[2] in ["不要", "no", "No"]]
    # 未回覆名單 = reply.db 有出現過但今天沒寫入 replies 的 user
    no_reply_list = [name for uid, name in all_users if uid not in replied_user_ids]
    return yes_list, no_list, no_reply_list

# 新增程式碼
def get_name_from_config(user_id):
    config_path = "users_config.json"
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