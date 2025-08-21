from flask import Flask, request, abort
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from config import config
from database.db import init_db
from services.message_service import MessageService
from scheduler import start_scheduler
import logging
import os

# ✅ 設定 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ✅ 初始化 Flask 應用
app = Flask(__name__)

# ✅ 初始化 LINE 設定
channel_secret = config.LINE_CHANNEL_SECRET
channel_access_token = config.LINE_CHANNEL_ACCESS_TOKEN

if not channel_secret or not channel_access_token:
    logger.error("請設定 LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN")
    exit(1)

handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)
line_bot_api = MessagingApi(ApiClient(configuration))

# 初始化訊息服務
message_service = MessageService(line_bot_api)

# ✅ Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature. Check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# ✅ 處理訊息事件
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理 LINE 訊息事件"""
    message_service.handle_message(event)

# ✅ 初始化（給 Gunicorn 或本地開發使用）
init_db()

def main():
    print("✅ Running local Flask server")
    # 本地執行時啟動排程器
    start_scheduler()
    flask_config = config.get_flask_config()
    app.run(**flask_config)

# ✅ 若是本地執行，跑 main()（含 scheduler 與 app.run）
# ✅ 若是 Gunicorn，則由環境變數控制是否啟動 scheduler
if __name__ == "__main__":
    main()
elif os.environ.get("RUN_SCHEDULER") == "true":
    print("✅ Starting scheduler under Gunicorn")
    # Gunicorn 環境下啟動排程器
    start_scheduler()
else:
    print("ℹ️ 排程器未啟動（僅在本地執行或 RUN_SCHEDULER=true 時啟動）")
