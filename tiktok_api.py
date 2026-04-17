#!/usr/bin/env python3
"""
TikTok Content Posting API
Правильная публикация видео через S3 presigned URL
"""

import os
import json
import requests
import time
import hashlib
import http.server
import socketserver
import threading
from datetime import datetime
from pathlib import Path
from tiktok_config import (
    TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET,
    TIKTOK_API_BASE, TOKEN_FILE
)

# ============ CONSTANTS ============
MAX_VIDEO_SIZE_MB = 500
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024
SUPPORTED_FORMATS = [".mp4", ".mov", ".avi", ".mkv"]

# ============ COLORS ============
class C:
    G, Y, R, B, BOLD, END = '\033[92m', '\033[93m', '\033[91m', '\033[94m', '\033[1m', '\033[0m'

def cg(t): return f"{C.G}{t}{C.END}"
def cy(t): return f"{C.Y}{t}{C.END}"
def cr(t): return f"{C.R}{t}{C.END}"
def cbold(t): return f"{C.BOLD}{t}{C.END}"


def log(msg, lvl="info"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if lvl == "success": p, m = "[OK]", cg(msg)
    elif lvl == "error": p, m = "[ERR]", cr(msg)
    elif lvl == "warning": p, m = "[WARN]", cy(msg)
    elif lvl == "info": p, m = "[INFO]", cy(msg)
    else: p, m = "", msg
    print(f"[{ts}] {p} {m}")


# ============ VIDEO VALIDATION ============
class VideoValidationError(Exception):
    """Кастомная ошибка валидации видео"""
    pass


def validate_video(video_path):
    """
    Валидация видео перед загрузкой
    
    Args:
        video_path: Путь к видео
    
    Returns:
        tuple: (is_valid, error_message)
    """
    path = Path(video_path)
    
    # Проверка существования
    if not path.exists():
        return False, f"File not found: {video_path}"
    
    # Проверка расширения
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        return False, f"Unsupported format: {path.suffix}. Use: {', '.join(SUPPORTED_FORMATS)}"
    
    # Проверка размера
    file_size = path.stat().st_size
    if file_size > MAX_VIDEO_SIZE_BYTES:
        size_mb = file_size / 1024 / 1024
        return False, f"File too large: {size_mb:.1f}MB (max {MAX_VIDEO_SIZE_MB}MB)"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Проверка минимального размера (10KB - явно битый файл)
    if file_size < 10240:
        return False, f"File too small: {file_size} bytes (possible corrupted)"
    
    return True, None


class VideoHandler(http.server.SimpleHTTPRequestHandler):
    video_path = None
    
    def do_GET(self):
        if self.video_path and os.path.exists(self.video_path):
            self.send_response(200)
            self.send_header('Content-type', 'video/mp4')
            self.send_header('Content-Length', str(os.path.getsize(self.video_path)))
            self.end_headers()
            with open(self.video_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass


def start_video_server(video_path, port=8090):
    """Запуск HTTP сервера для раздачи видео"""
    VideoHandler.video_path = video_path
    
    class TCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    
    server = TCPServer(("localhost", port), VideoHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    return server, f"http://localhost:{port}/video"


# ============ TOKEN MANAGEMENT ============
def load_token():
    """Загрузка токена с проверкой срока"""
    if not os.path.exists(TOKEN_FILE):
        return None
    
    try:
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
        
        # Проверяем expires_at (добавляем если нет)
        if "expires_at" not in data:
            data["expires_at"] = time.time() + data.get("expires_in", 3600)
            save_token(data)
        
        return data
    except json.JSONDecodeError as e:
        log(f"Token file corrupted: {e}", "error")
        # Резервное копирование
        try:
            backup_path = TOKEN_FILE + ".backup"
            os.rename(TOKEN_FILE, backup_path)
            log(f"Backup saved: {backup_path}", "info")
        except:
            pass
        return None
    except Exception as e:
        log(f"Token load error: {e}", "error")
        return None


def save_token(token_data):
    """Сохранение токена"""
    token_data["expires_at"] = time.time() + token_data.get("expires_in", 86400)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    log("Token saved", "success")


def refresh_token():
    """Обновление токена через refresh_token"""
    token = load_token()
    if not token:
        return None
    
    refresh = token.get("refresh_token")
    if not refresh:
        log("No refresh_token in file", "error")
        return None
    
    data = {
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh
    }
    
    log("Refreshing token...", "info")
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data=data)
    
    if r.status_code == 200:
        new_token = r.json()
        save_token(new_token)
        log("Token refreshed successfully", "success")
        return new_token
    else:
        log(f"Refresh failed: {r.status_code} - {r.text}", "error")
        return None


def get_access_token():
    """Получение валидного access_token с авто-refresh"""
    token = load_token()
    
    if not token:
        log("No token file. Run: python tiktok_auth.py", "error")
        return None
    
    # Проверяем срок (обновляем за 5 минут до истечения)
    expires_at = token.get("expires_at", 0)
    if time.time() > expires_at - 300:
        log("Token expired or expiring soon, refreshing...", "info")
        token = refresh_token()
        if not token:
            return None
    
    return token.get("access_token")


# ============ VIDEO PUBLISHING ============
def init_video_upload(access_token, title="Video #fyp", video_size=0, video_url=None):
    """
    Инициализация загрузки видео
    Возвращает (upload_token, upload_url) или (None, None)
    """
    url = f"{TIKTOK_API_BASE}/post/publish/video/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    if video_url:
        data = {
            "post_info": {
                "title": title,
                "privacy_level": "SELF_ONLY",
                "disable_comment": False,
                "disable_duet": False,
                "disable_stitch": False
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url
            }
        }
    else:
        data = {
            "post_info": {
                "title": title,
                "privacy_level": "SELF_ONLY",
                "disable_comment": False,
                "disable_duet": False,
                "disable_stitch": False
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1
            }
        }
    
    r = requests.post(url, headers=headers, json=data)
    
    if r.status_code == 200:
        resp = r.json()
        upload_data = resp.get("data", {})
        publish_id = upload_data.get("publish_id")
        upload_url = upload_data.get("upload_url")
        
        log(f"Upload initialized", "success")
        log(f"  publish_id: {publish_id[:30]}..." if publish_id else "  No publish_id", "info")
        log(f"  upload_url: {upload_url[:50]}..." if upload_url else "  No upload_url", "info")
        
        return publish_id, upload_url
    else:
        log(f"Init failed: {r.status_code}", "error")
        log(f"Response: {r.text}", "error")
        return None, None


def upload_to_s3(upload_url, video_path):
    """
    Загрузка видео на S3 через presigned URL
    TikTok выдаёт S3 presigned URL для прямой загрузки
    """
    file_size = os.path.getsize(video_path)
    log(f"Uploading {video_path} ({file_size / 1024 / 1024:.2f} MB)", "info")
    
    chunk_size = 5 * 1024 * 1024
    offset = 0
    
    with open(video_path, "rb") as f:
        while offset < file_size:
            chunk = f.read(min(chunk_size, file_size - offset))
            end = offset + len(chunk) - 1
            
            headers = {
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes {offset}-{end}/{file_size}"
            }
            
            r = requests.put(upload_url, data=chunk, headers=headers)
            
            if r.status_code not in [200, 201, 204]:
                log(f"S3 upload failed: {r.status_code}", "error")
                log(f"Response: {r.text[:500] if r.text else 'Empty'}", "error")
                return False
            
            offset = end + 1
            log(f"Uploaded {offset}/{file_size} bytes", "info")
    
    log("Video uploaded to S3", "success")
    return True


def check_publish_status(access_token, upload_token):
    """Проверка статуса публикации"""
    url = f"{TIKTOK_API_BASE}/post/publish/status/fetch/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {"publish_id": upload_token}
    
    r = requests.post(url, headers=headers, json=data)
    
    if r.status_code == 200:
        resp = r.json()
        data_resp = resp.get("data", {})
        status = data_resp.get("status")
        
        # Логируем дополнительную информацию
        if status == "PUBLISH_FAILED":
            error_info = data_resp.get("error", {})
            log(f"Publish error: {error_info}", "error")
        
        log(f"Publish status: {status}", "info")
        return status
    else:
        log(f"Status check failed: {r.text}", "error")
        return None


def publish_video(video_path, title="Video #fyp #viral", max_retries=5, wait_time=15):
    """
    Публикация видео в TikTok
    
    Args:
        video_path: Путь к MP4 файлу
        title: Заголовок видео с хештегами
        max_retries: Максимум попыток проверки статуса
        wait_time: Пауза между проверками статуса (сек)
    
    Returns:
        dict: {"success": bool, "publish_id": str, "error": str}
    """
    log(f"Publishing: {video_path}", "info")
    log(f"Title: {title}", "info")
    
    # Валидация видео
    is_valid, error_msg = validate_video(video_path)
    if not is_valid:
        log(f"Validation failed: {error_msg}", "error")
        return {"success": False, "publish_id": None, "error": error_msg}
    
    # Получаем токен
    access_token = get_access_token()
    if not access_token:
        return {"success": False, "publish_id": None, "error": "Cannot get access token"}
    
    # Инициализация FILE_UPLOAD
    file_size = os.path.getsize(video_path)
    publish_id, upload_url = init_video_upload(access_token, title, file_size)
    if not upload_url:
        return {"success": False, "publish_id": None, "error": "Failed to get upload URL"}
    
    # Загрузка на S3
    if not upload_to_s3(upload_url, video_path):
        return {"success": False, "publish_id": publish_id, "error": "S3 upload failed"}
    
    # Проверка статуса (даём TikTok время обработать)
    log("Waiting for processing...", "info")
    time.sleep(5)
    
    for attempt in range(max_retries):
        status = check_publish_status(access_token, publish_id)
        
        if status == "PUBLISH_COMPLETE":
            log("Video published successfully!", "success")
            return {"success": True, "publish_id": publish_id, "error": None}
        
        elif status == "PUBLISH_FAILED":
            log("Publish failed", "error")
            return {"success": False, "publish_id": publish_id, "error": "Publish failed"}
        
        elif status in ["PROCESSING", "UPLOAD_COMPLETE", "PENDING"]:
            log(f"Status: {status}, waiting... ({attempt + 1}/{max_retries})", "info")
            time.sleep(wait_time)
        else:
            log(f"Unknown status: {status}", "warning")
            if attempt < max_retries - 1:
                time.sleep(wait_time)
    
    log("Timeout waiting for publish", "error")
    return {"success": False, "publish_id": publish_id, "error": "Timeout"}


# ============ UTILITY FUNCTIONS ============
def check_video_md5(video_path):
    """Получить MD5 хеш видео для отладки"""
    md5 = hashlib.md5()
    with open(video_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def get_video_info(video_path):
    """Получить информацию о видео"""
    path = Path(video_path)
    if not path.exists():
        return None
    
    stat = path.stat()
    return {
        "name": path.name,
        "size_mb": round(stat.st_size / 1024 / 1024, 2),
        "format": path.suffix.lower(),
        "md5": check_video_md5(video_path)
    }


# ============ TEST ============
if __name__ == "__main__":
    log("TikTok Content Posting API", "info")
    log(f"Client Key: {TIKTOK_CLIENT_KEY[:10]}...", "info")
    
    # Проверяем токен
    token = load_token()
    if token:
        expires_at = token.get("expires_at", 0)
        remaining = expires_at - time.time()
        
        if remaining > 0:
            log(f"Token valid for {remaining / 60:.1f} minutes", "success")
            log(f"Open ID: {token.get('open_id', 'N/A')[:20]}...", "info")
        else:
            log("Token expired, need refresh", "error")
            
            # Пробуем refresh
            if refresh_token():
                log("Token refreshed!", "success")
            else:
                log("Refresh failed. Run: python tiktok_auth.py", "error")
    else:
        log("No token. Run: python tiktok_auth.py", "error")
    
    # Проверка тестового видео
    test_video = "test_video.mp4"
    if os.path.exists(test_video):
        log("\nTest video info:", "info")
        info = get_video_info(test_video)
        if info:
            for k, v in info.items():
                log(f"  {k}: {v}", "info")