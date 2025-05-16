import os

class Config:
    # Telegram API credentials
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", None)
    BOT_TOKEN = os.environ.get("BOT_TOKEN", None)
    
    # Assistant account (user account that will join voice chats)
    # Either use session string or phone number
    SESSION_STRING = os.environ.get("SESSION_STRING", None)
    PHONE_NUMBER = os.environ.get("PHONE_NUMBER", None)
    
    # Bot settings
    PREFIX = "!"  # Command prefix
    ADMINS = list(map(int, os.environ.get("ADMINS", "").split())) if os.environ.get("ADMINS") else []
    
    # Music settings
    MAX_PLAYLIST_SIZE = 10
    DURATION_LIMIT = 120  # In minutes
    
    # Paths
    DOWNLOAD_PATH = "downloads/"
    
    @classmethod
    def validate(cls):
        """Validate required configuration variables"""
        missing = []
        if not cls.API_ID:
            missing.append("API_ID")
        if not cls.API_HASH:
            missing.append("API_HASH")
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        if not cls.SESSION_STRING and not cls.PHONE_NUMBER:
            missing.append("SESSION_STRING or PHONE_NUMBER")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Create download directory if it doesn't exist
        if not os.path.exists(cls.DOWNLOAD_PATH):
            os.makedirs(cls.DOWNLOAD_PATH)

# Validate config at import time
Config.validate()
