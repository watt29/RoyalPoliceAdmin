import os
from dotenv import load_dotenv  # type: ignore

# Clear any existing TELEGRAM_BOT_TOKEN to ensure .env takes precedence
if 'TELEGRAM_BOT_TOKEN' in os.environ:
    os.environ.pop('TELEGRAM_BOT_TOKEN', None) # type: ignore


# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the Telegram Memo Bot"""
    
    # Telegram Configuration - Force reload from environment
    @property
    def TELEGRAM_BOT_TOKEN(self):
        return os.getenv('TELEGRAM_BOT_TOKEN')
    
    @property
    def ADMIN_CHAT_ID(self):
        return os.getenv('ADMIN_CHAT_ID')


    # Google Sheets Configuration
    GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Smart_Memo_Database')
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1xxwyReavlHXmKqEIEdem7zUAdlVS5Kv2D_7S6Rsf2UA')
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'service_account.json')
    GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1W7HAAqSSLNpRMmIKbtqjmm_ayp_PnBOT')
    SERVICE_ACCOUNT_EMAIL = os.getenv('SERVICE_ACCOUNT_EMAIL', 'telegram-memo-bot@telegram-smart-memo.iam.gserviceaccount.com')
    
    # Drive Automation
    ENABLE_DRIVE = os.getenv('ENABLE_DRIVE', 'False').lower() == 'true'
    
    # Bot Configuration
    MAX_SEARCH_RESULTS = 5
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        config = cls()
        required_vars = ['TELEGRAM_BOT_TOKEN', 'GOOGLE_CREDENTIALS_PATH']
        
        missing_vars = []
        for var in required_vars:
            if not getattr(config, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Check if credentials file exists
        if not os.path.exists(config.GOOGLE_CREDENTIALS_PATH):
            raise FileNotFoundError(f"Google credentials file not found: {config.GOOGLE_CREDENTIALS_PATH}")
        
        return True
