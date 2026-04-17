#!/usr/bin/env python3
"""
TikTok API Configuration
Загружает credentials из переменных окружения (.env файл)
"""

import os
from dotenv import load_dotenv

# Загрузка .env файла
load_dotenv()

# API Credentials (из переменных окружения)
TIKTOK_CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "")

# OAuth endpoints
TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

# API endpoints
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

# Default redirect URI (localhost для OAuth callback)
REDIRECT_URI = os.environ.get("TIKTOK_REDIRECT_URI", "http://localhost:8080/callback")

# Scopes (разрешения) - базовые для Content Posting API
SCOPES = ["user.info.basic", "video.upload", "video.publish"]

# Token file (абсолютный путь)
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "tiktok_token.json")

# Проверка наличия credentials
if not TIKTOK_CLIENT_KEY or not TIKTOK_CLIENT_SECRET:
    raise EnvironmentError(
        "❌ Missing credentials!\n"
        "   Create .env file with:\n"
        "   TIKTOK_CLIENT_KEY=your_client_key\n"
        "   TIKTOK_CLIENT_SECRET=your_client_secret"
    )