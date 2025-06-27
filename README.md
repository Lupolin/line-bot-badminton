🏸 LINE 羽球出席統計系統
本系統是一個使用 LINE Bot + Flask 打造的互動統計系統，能定時詢問群組成員是否出席羽球活動，並統計回覆結果，最終產出出席報告，協助活動籌劃與場地安排。

✨ 功能特色
🕒 定時推播：依照 users_config.json 設定，自動發送「要不要打羽球」或出席統計摘要訊息

🗣️ 簡單互動：使用者只需傳送「要」或「不要」即可完成回覆

📊 出席統計：傳送「統計」或「羽球」關鍵字即可取得當日出席統計

👤 自動辨識暱稱：根據 LINE ID 自動對應使用者暱稱

💾 本地資料儲存：使用 SQLite 資料庫保存所有回覆紀錄

🗂️ 專案結構
bash
Copy
Edit
.
├── app.py # 主程式，處理 LINE webhook 與訊息邏輯
├── scheduler.py # 定時訊息推播邏輯
├── db.py # SQLite 操作模組（回覆資料存取）
├── line_service.py # 處理 LINE API 發送與接收
├── users_config.json # 使用者與通知時間設定
├── reply.db # SQLite 回覆資料庫（自動產生）
├── .env # 儲存 LINE channel 憑證
└── README.md # 專案說明文件
⚙️ 安裝與啟動

1. 安裝必要套件
   bash
   Copy
   Edit
   pip install flask line-bot-sdk python-dotenv apscheduler
2. 設定 .env 檔案
   在根目錄建立 .env，並輸入你的 LINE Bot 憑證：

ini
Copy
Edit
LINE_CHANNEL_ACCESS_TOKEN=你的 ChannelAccessToken
LINE_CHANNEL_SECRET=你的 ChannelSecret 3. 啟動應用程式
bash
Copy
Edit
python app.py 4. 使用 ngrok 暴露 webhook
bash
Copy
Edit
ngrok http 5000
將 ngrok 提供的網址填入 LINE Developers 的 Webhook URL，例如：

arduino
Copy
Edit
https://xxxxxx.ngrok.io/callback
👥 新增/編輯使用者設定
請編輯 users_config.json，加入使用者區塊：

json
Copy
Edit
{
"user_id": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"name": "Lucas",
"notification_times": [
{ "day": "wednesday", "hour": 18, "minute": 30, "type": "ask" },
{ "day": "wednesday", "hour": 22, "minute": 0, "type": "summary" }
]
}
type: "ask" → 發送「今天要打羽球嗎？」訊息

type: "summary" → 傳送出席統計摘要

新增或修改後重新啟動 app.py 以套用變更。

📊 使用說明
使用者互動：
操作 說明
傳送「要」 登記為當日要打羽球
傳送「不要」 登記為當日不打羽球
傳送「統計」或「羽球」 顯示今日出席統計結果

🧪 開發建議與擴充方向
顯示「尚未回覆」的使用者名單

美化訊息內容，改用 Flex Message 呈現

擴充至其他活動問卷（如籃球、聚餐等）

建立 Web UI 管理 users_config.json 設定

支援遠端資料庫與 ORM 儲存架構

🪪 授權
本專案採用 MIT License，歡迎自由修改與散佈。
