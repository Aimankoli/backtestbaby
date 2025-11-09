import os
from dotenv import load_dotenv

load_dotenv()

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 1

# Cookie settings
COOKIE_NAME = "access_token"
COOKIE_HTTPONLY = True
COOKIE_SECURE = False  # Set to True in production with HTTPS
COOKIE_SAMESITE = "lax"
COOKIE_MAX_AGE = 86400  # 1 day in seconds

# MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = "BacktestMCP"

# Dedalus
DEDALUS_API_KEY = os.getenv("DEDALUS_API_KEY")
DEFAULT_MODEL = "openai/gpt-4.1"

# Twitter/X API
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")
