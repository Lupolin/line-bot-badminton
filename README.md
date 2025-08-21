🏸 LINE 羽球出席統計系統
本系統是一個使用 LINE Bot + Flask 打造的互動統計系統，能定時詢問群組成員是否出席羽球活動，並統計回覆結果，最終產出出席報告，協助活動籌劃與場地安排。

✨ 功能特色
🕒 定時推播：依照 users_config.json 設定，自動發送「要不要打羽球」或出席統計摘要訊息

🗣️ 簡單互動：使用者只需傳送「要」或「不要」即可完成回覆

📊 出席統計：傳送「統計」或「羽球」關鍵字即可取得當日出席統計

👤 自動辨識暱稱：根據 LINE ID 自動對應使用者暱稱

💾 資料儲存：使用 MySQL/RDS 資料庫保存所有回覆紀錄

🔧 統一配置管理：所有設定參數集中管理，易於維護

🗂️ 專案結構

```
.
├── app.py               # 主程式，處理 LINE webhook 與訊息邏輯
├── scheduler.py         # 定時訊息推播（cron 到點觸發）
├── config.py            # 🔧 統一配置管理系統
├── line_service.py      # 處理 LINE API 推播
├── requirements.txt     # 套件清單
├── users_config.json    # 使用者與通知時間設定
├── README.md            # 專案說明文件
├── database/
│   └── db.py            # MySQL/RDS 資料存取
├── services/
│   ├── message_service.py       # 解析指令與互動
│   └── notification_service.py  # 問訊與統計推播
└── utils/
    └── date_utils.py    # 日期工具（取得週五等）
```

⚙️ 安裝與啟動

1. 安裝必要套件

   ```bash
   pip install -r requirements.txt
   ```

2. 設定環境變數
   複製 `.env.example` 為 `.env`，並填入你的設定：

   - macOS/Linux

   ```bash
   cp .env.example .env
   ```

   - Windows (PowerShell)

   ```powershell
   copy .env.example .env
   ```

   在 `.env` 檔案中設定：

   ```ini
   # LINE Bot 配置
   LINE_CHANNEL_ACCESS_TOKEN=你的 ChannelAccessToken
   LINE_CHANNEL_SECRET=你的 ChannelSecret

   # 資料庫配置 (RDS)
   RDS_HOST=你的資料庫主機
   RDS_PORT=3306
   RDS_USER=資料庫使用者名
   RDS_PASSWORD=資料庫密碼
   RDS_DATABASE=資料庫名稱
   RDS_SSL_CA=SSL憑證路徑  # 可選

   # Flask 應用配置
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5003
   FLASK_DEBUG=false
   ```

3. 啟動應用程式

   ```bash
   python app.py
   ```

   說明：

   - 本地執行時會自動啟動排程（APScheduler）。
   - 若以 Gunicorn/其他 WSGI 方式部署，請設定環境變數 `RUN_SCHEDULER=true` 才會啟動排程。

4. 使用 ngrok 暴露 webhook
   ```bash
   ngrok http 5003
   ```
   將 ngrok 提供的網址填入 LINE Developers 的 Webhook URL，例如：
   ```
   https://xxxxxx.ngrok.io/callback
   ```

🔧 配置系統說明

本系統使用統一的配置管理，所有設定都在 `config.py` 中：

- **LINE Bot 配置**：Channel Secret、Access Token
- **資料庫配置**：RDS 連線參數
- **Flask 配置**：主機、埠號、除錯模式
- **羽球活動配置**：地點、時間、日期
- **通知配置**：cron 到點觸發（依 `users_config.json`）；每週日 21:00 自動重置回覆
- **關鍵字配置**：各種指令的觸發關鍵字

如需修改配置，請編輯 `config.py` 檔案，或透過環境變數覆蓋預設值。

👥 新增/編輯使用者設定
請編輯 users_config.json，加入使用者區塊：

```json
{
  "users": [
    {
      "user_id": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "name": "Lucas",
      "notification_times": [
        { "day": "wednesday", "hour": 18, "minute": 30, "type": "ask" },
        { "day": "wednesday", "hour": 22, "minute": 0, "type": "summary" }
      ]
    }
  ]
}
```

- `type: "ask"` → 發送「今天要打羽球嗎？」訊息
- `type: "summary"` → 傳送出席統計摘要

新增或修改後重新啟動 app.py 以套用變更。

🕒 發信機制

- 使用 APScheduler 的 cron 觸發，依 `users_config.json` 逐一為每位使用者建立排程。
- `type: "ask"` 時會發送詢問訊息；若該使用者已回覆，會自動跳過不重發。
- `type: "summary"` 時會發送當前出席統計摘要（要/不要/未回覆）。
- 週日 21:00（Asia/Taipei）自動重置所有人的回覆狀態。
- 時區使用 `Asia/Taipei`。

📊 使用說明
使用者互動：
| 操作 | 說明 |
|------|------|
| 傳送「要」 | 登記為當日要打羽球 |
| 傳送「不要」 | 登記為當日不打羽球 |
| 傳送「統計」或「本週球友」 | 顯示今日出席統計結果 |
| 傳送「通知」或「提醒」 | 手動發送提醒通知 |
| 傳送「幫助」 | 顯示使用說明 |
| 傳送「導航」或「地圖」 | 取得球場位置導航 |

🧪 開發建議與擴充方向

- 顯示「尚未回覆」的使用者名單
- 美化訊息內容，改用 Flex Message 呈現
- 擴充至其他活動問卷（如籃球、聚餐等）
- 建立 Web UI 管理 users_config.json 設定
- 支援更多資料庫類型與 ORM 儲存架構

🪪 授權
本專案採用 MIT License，歡迎自由修改與散佈。
