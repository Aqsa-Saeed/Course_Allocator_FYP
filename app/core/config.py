"""
App settings, pulled from environment variables (or .env via dotenv).
SECRET_KEY must be overridden in production:
    python -c "import secrets; print(secrets.token_hex(32))"
"""

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
