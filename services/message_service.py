import logging
import urllib.parse
from linebot.v3.messaging import (
    ReplyMessageRequest, TextMessage,
    TemplateMessage, ButtonsTemplate, URIAction
)
from database.db import get_user_reply, has_replied, update_reply, insert_reply, get_name_from_config
from config import config
from utils.date_utils import get_friday
from datetime import datetime

# 設定 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 確保 logger 有 handler
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class MessageService:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api

    def handle_message(self, event):
        """處理 LINE 訊息事件"""
        # 添加 debug 資訊追蹤調用來源
        event_id = getattr(event.message, 'id', 'unknown')
        current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        logger.info(f"🔍 [DEBUG] handle_message 被調用 - 時間: {current_time}, 事件ID: {event_id}")
        
        friday_str = get_friday()

        try:
            user_id = event.source.user_id
            reply_text = event.message.text.strip()
            user_name = get_name_from_config(user_id)

            logger.info(f"[MessageEvent] 使用者 {user_id}（{user_name}）輸入：{reply_text}")

            # 📊 查詢統計
            if reply_text in config.STAT_KEYWORDS:
                self._handle_stats_request(event, friday_str)
                return

            # ✅ 回覆「要 / 不要」
            if reply_text in config.YES_KEYWORDS + config.NO_KEYWORDS:
                self._handle_reply(event, user_id, user_name, reply_text)
                return
            
            # 通知 / 提醒
            if reply_text in config.NOTIFY_KEYWORDS:
                self._handle_notify_request(event, user_id, user_name)
                return
            
            # 幫助
            if reply_text in config.HELP_KEYWORDS:
                self._handle_help_request(event)
                return
            
            # 導航 / 地圖
            if reply_text in config.MAP_KEYWORDS:
                self._handle_map_request(event)
                return
            
        except Exception as e:
            logger.error("[Unhandled error in handle_message] %s", e)

    def _handle_stats_request(self, event, friday_str):
        """處理統計請求"""
        yes_list, no_list, no_reply_list = get_user_reply()
        yes_names = "\n".join(f"- {name}" for name in yes_list)
        no_names = "\n".join(f"- {name}" for name in no_list)
        no_reply_names = "\n".join(f"- {name}" for name in no_reply_list)
        
        response = f"出席統計（{friday_str}）\n"
        response += f"✅ 要打球（{len(yes_list)}人）:\n{yes_names or '（無）'}\n\n"
        response += f"❌ 不打球（{len(no_list)}人）:\n{no_names or '（無）'}\n\n"
        response += f"😡 未回應（{len(no_reply_list)}人）:\n{no_reply_names or '（無）'}"
        
        self._reply(event, response)

    def _handle_reply(self, event, user_id, user_name, reply_text):
        """處理回覆（要/不要）"""
        try:
            if has_replied(user_id):
                updated = update_reply(user_id, reply_text)
                if updated:
                    logger.info(f"[記錄更新] {user_name} 已更新為「{reply_text}」")
                else:
                    logger.info(f"[記錄略過] {user_name} 已回覆相同內容「{reply_text}」，略過")
            else:
                insert_reply(user_id, user_name, reply_text)
                logger.info(f"[記錄新增] {user_name} 回覆「{reply_text}」")
        except Exception as e:
            logger.error("[資料庫錯誤] %s", e)

    def _handle_notify_request(self, event, user_id, user_name):
        """處理通知請求"""
        # 延遲導入避免循環 import
        from services.notification_service import send_ask_notification
        
        user = {
            "user_id": user_id,
            "name": user_name
        }
        send_ask_notification(user)
        self._reply(event, "已發送提醒通知！")

    def _handle_help_request(self, event):
        """處理幫助請求"""
        response = (
            "可用指令：\n"
            "- 統計：查看出席統計\n"
            "- 要 / 不要：回覆是否參加活動\n"
            "- 通知 / 提醒：發送提醒通知\n"
            "- 幫助 / Help：顯示這個幫助訊息\n"
            "- 貿協的秘密：查看貿協的秘密"
        )
        self._reply(event, response)

    def _handle_map_request(self, event):
        """處理地圖請求"""
        destination = config.BADMINTON_LOCATION
        encoded_destination = urllib.parse.quote(destination)
        map_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_destination}"

        buttons_template = ButtonsTemplate(
            title=f"導航至{config.BADMINTON_LOCATION}",
            text="點選下方按鈕，開始導航",
            actions=[URIAction(label="開啟 Google 導航", uri=map_url)]
        )

        template_message = TemplateMessage(
            alt_text=f"導航到{config.BADMINTON_LOCATION}",
            template=buttons_template
        )

        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[template_message]
            )
        )

    def _reply(self, event, text):
        """發送回覆訊息"""
        try:
            self.line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=text)]
                )
            )
        except Exception as e:
            logger.error("[Reply error] %s", e)
