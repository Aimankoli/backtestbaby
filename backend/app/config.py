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
