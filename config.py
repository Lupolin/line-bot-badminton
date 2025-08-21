import os
from typing import Optional
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

class Config:
    """統一配置管理類別"""
    
    # LINE Bot 配置
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    
    # 資料庫配置
    DB_HOST = os.getenv("RDS_HOST")
    DB_PORT = int(os.getenv("RDS_PORT", "3306"))
    DB_USER = os.getenv("RDS_USER")
    DB_PASSWORD = os.getenv("RDS_PASSWORD")
    DB_NAME = os.getenv("RDS_DATABASE")
    DB_SSL_CA = os.getenv("RDS_SSL_CA")  # 可為空
    DB_TABLE = "badminton_reply"
    
    # Flask 應用配置
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5003"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    # 時區配置
    TIMEZONE = "Asia/Taipei"
    
    # 檔案路徑配置
    USERS_CONFIG_PATH = "users_config.json"
    
    # 羽球活動配置
    BADMINTON_LOCATION = "臺北市信義區信義國民小學"
    BADMINTON_TIME = "18:00-20:00"
    BADMINTON_DAY = "friday"
    
    # 通知配置
    RESET_REPLIES_TIME = "21:00"  # 重置回覆狀態時間（週日）
    RESET_REPLIES_DAY = "sun"
    
    # 回應關鍵字配置
    YES_KEYWORDS = ["要", "Yes", "yes"]
    NO_KEYWORDS = ["不要", "No", "no"]
    STAT_KEYWORDS = ["本週球友", "統計", "Stat", "stat", "統計資料", "統計數據"]
    NOTIFY_KEYWORDS = ["發出召集令", "通知", "提醒", "Send", "send"]
    HELP_KEYWORDS = ["使用說明", "幫助", "Help", "help"]
    MAP_KEYWORDS = ["球場怎麼去", "導航", "地圖", "位置", "Map", "map"]
    
    @classmethod
    def validate_required_configs(cls) -> bool:
        """驗證必要的配置是否已設定"""
        required_configs = [
            ("LINE_CHANNEL_SECRET", cls.LINE_CHANNEL_SECRET),
            ("LINE_CHANNEL_ACCESS_TOKEN", cls.LINE_CHANNEL_ACCESS_TOKEN),
            ("RDS_HOST", cls.DB_HOST),
            ("RDS_USER", cls.DB_USER),
            ("RDS_PASSWORD", cls.DB_PASSWORD),
            ("RDS_DATABASE", cls.DB_NAME),
        ]
        
        missing_configs = []
        for config_name, config_value in required_configs:
            if not config_value:
                missing_configs.append(config_name)
        
        if missing_configs:
            print(f"❌ 缺少必要的環境變數: {', '.join(missing_configs)}")
            return False
        
        return True
    
    @classmethod
    def get_database_config(cls) -> dict:
        """取得資料庫連線配置"""
        config = {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
            "database": cls.DB_NAME,
            "charset": "utf8mb4",
            "connect_timeout": 10,
            "autocommit": False,
        }
        
        if cls.DB_SSL_CA:
            config["ssl"] = {"ca": cls.DB_SSL_CA}
        
        return config
    
    @classmethod
    def get_flask_config(cls) -> dict:
        """取得 Flask 配置"""
        return {
            "host": cls.FLASK_HOST,
            "port": cls.FLASK_PORT,
            "debug": cls.FLASK_DEBUG
        }
    
    @classmethod
    def print_config_summary(cls):
        """印出配置摘要（用於除錯）"""
        print("🔧 配置摘要:")
        print(f"  LINE Bot: {'✅' if cls.LINE_CHANNEL_SECRET and cls.LINE_CHANNEL_ACCESS_TOKEN else '❌'}")
        print(f"  資料庫: {'✅' if cls.DB_HOST and cls.DB_USER and cls.DB_PASSWORD else '❌'}")
        print(f"  Flask: {cls.FLASK_HOST}:{cls.FLASK_PORT} (debug: {cls.FLASK_DEBUG})")
        print(f"  時區: {cls.TIMEZONE}")
        print(f"  羽球地點: {cls.BADMINTON_LOCATION}")
        print(f"  羽球時間: {cls.BADMINTON_TIME}")

# 建立全域配置實例
config = Config()

# 驗證配置
if not config.validate_required_configs():
    raise ValueError("配置驗證失敗，請檢查環境變數設定")
