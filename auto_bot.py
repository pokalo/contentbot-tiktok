#!/usr/bin/env python3
"""
Auto AI Bot - полная автоматизация
Скачивает -> обрабатывает AI -> публикует в TikTok
"""

import os
import sys
import time
import json
import subprocess
import shutil
import requests
import re
from pathlib import Path
from datetime import datetime

# ============ КОНФИГУРАЦИЯ ============
DOWNLOADS = "downloads"
PROCESSED = "processed"
TOKEN_FILE = "tiktok_token.json"
LOG_FILE = "bot_log.txt"
MAX_TIKTOK_DURATION = 10  # Макс. 10 секунд для неодобренных приложений

# ============ ЛОГИРОВАНИЕ ============
def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    text = f"[{ts}] [{level}] {msg}"
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def get_video_duration(video_path):
    """Получить длительность видео в секундах"""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
           "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return None

# ============ ШАГ 1: СКАЧИВАНИЕ ============
def download_video(url):
    """Скачать видео по URL"""
    os.makedirs(DOWNLOADS, exist_ok=True)
    
    filename = f"input_{int(time.time())}.mp4"
    filepath = os.path.join(DOWNLOADS, filename)
    
    log(f"Downloading: {url[:50]}...")
    
    cmd = ["yt-dlp", "-o", filepath, "--no-warnings", url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=180)
        
        # Найти скачанный файл
        files = [f for f in os.listdir(DOWNLOADS) if f.endswith(".mp4") and f.startswith("input")]
        if files:
            latest = max([os.path.join(DOWNLOADS, f) for f in files], key=os.path.getmtime)
            log(f"Downloaded: {latest}")
            return latest
        
    except Exception as e:
        log(f"Download error: {e}")
    
    return None

# ============ ШАГ 2: AI ОБРАБОТКА ============
USE_COMFY = False  # ComfyUI API nodes require login - use ffmpeg instead

def process_video_local(input_path):
    """Обработка через локальный ffmpeg - улучшенная версия"""
    os.makedirs(PROCESSED, exist_ok=True)
    
    name = Path(input_path).stem
    output_path = os.path.join(PROCESSED, f"{name}_ai.mp4")
    
    # Проверить длительность
    duration = get_video_duration(input_path)
    if duration and duration > MAX_TIKTOK_DURATION:
        log(f"Video too long ({duration:.1f}s), trimming to {MAX_TIKTOK_DURATION}s...")
        # Сначала обрезать
        from video_processor import trim as trim_video
        temp_path = os.path.join(PROCESSED, f"{name}_trim.mp4")
        trimmed = trim_video(input_path, 0, MAX_TIKTOK_DURATION, temp_path)
        if trimmed:
            input_path = trimmed
    
    # Эффекты: насыщенность + яркость (используем -vf для видео)
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "eq=saturation=1.5:brightness=0.1",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "copy",
        output_path
    ]
    
    log("Applying AI effects...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=180)
        
        if result.returncode == 0 and os.path.exists(output_path):
            log(f"Processed: {output_path}")
            return output_path
        else:
            log(f"FFmpeg error: {result.stderr[:200]}", "ERROR")
    except Exception as e:
        log(f"Process error: {e}")
    
    return None

def process_video_comfy(input_path):
    """Обработка через ComfyUI AI"""
    os.makedirs(PROCESSED, exist_ok=True)
    
    try:
        from comfy_api import process_video_ai, check_comfy_status
        
        # Проверить что ComfyUI работает
        if not check_comfy_status():
            log("ComfyUI not available, falling back to ffmpeg", "WARN")
            return process_video_local(input_path)
        
        result = process_video_ai(
            input_path,
            effect="enhance",
            model="General Restore Model (2x)",
            resolution="720p"
        )
        
        if result and os.path.exists(result):
            # Проверить длительность
            duration = get_video_duration(result)
            if duration and duration > MAX_TIKTOK_DURATION:
                log(f"Video too long ({duration:.1f}s), trimming to {MAX_TIKTOK_DURATION}s...")
                from video_processor import trim as trim_video
                trimmed = trim_video(result, 0, MAX_TIKTOK_DURATION)
                if trimmed:
                    result = trimmed
            
            # Копируем в processed папку
            name = Path(input_path).stem
            output_path = os.path.join(PROCESSED, f"{name}_comfy.mp4")
            shutil.copy2(result, output_path)
            log(f"ComfyUI processed: {output_path}")
            return output_path
        
    except Exception as e:
        log(f"ComfyUI error: {e}", "ERROR")
    
    return process_video_local(input_path)

def process_video(input_path):
    """Выбрать способ обработки"""
    if USE_COMFY:
        log("Using ComfyUI AI...")
        return process_video_comfy(input_path)
    else:
        log("Using ffmpeg...")
        return process_video_local(input_path)

def get_ready_video():
    """Найти готовое видео для обработки"""
    if os.path.exists(DOWNLOADS):
        files = [os.path.join(DOWNLOADS, f) for f in os.listdir(DOWNLOADS) if f.endswith(".mp4")]
        if files:
            return max(files, key=os.path.getmtime)
    return None

# ============ ШАГ 3: ПУБЛИКАЦИЯ ============
def load_token():
    if not os.path.exists(TOKEN_FILE):
        log("No token! Run: python tiktok_auth.py", "ERROR")
        return None
    
    with open(TOKEN_FILE) as f:
        return json.load(f).get("access_token")

def publish_video(video_path, title="Auto video"):
    """Публикация в TikTok"""
    log(f"Publishing: {title}")
    
    token = load_token()
    if not token:
        return False, "No token"
    
    # Импорт API
    sys.path.insert(0, ".")
    try:
        from tiktok_api import publish_video as api_publish
        result = api_publish(video_path, title)
        
        if result.get("success"):
            log("Published!", "SUCCESS")
            return True, result.get("publish_id")
        else:
            log(f"Failed: {result.get('error')}", "ERROR")
            return False, result.get("error")
    except Exception as e:
        log(f"Publish error: {e}", "ERROR")
        return False, str(e)

# ============ ОСНОВНОЙ ЦИКЛ ============
def run_bot(source_url=None, max_videos=1):
    """
    Запустить бота
    
    Args:
        source_url: URL для скачивания (или None - использовать готовое)
        max_videos: сколько видео обработать
    """
    log("=== AUTO AI BOT STARTED ===")
    
    processed = 0
    
    # Если есть URL - скачиваем
    if source_url:
        video = download_video(source_url)
        if not video:
            log("Download failed", "ERROR")
            return
    
    # Иначе ищем готовое
    else:
        video = get_ready_video()
        if not video:
            log("No videos found", "ERROR")
            return
    
    # Обрабатываем
    processed_video = process_video(video)
    if not processed_video:
        log("Processing failed", "ERROR")
        return
    
    # Публикуем
    title = f"AI processed video #{processed+1}"
    success, info = publish_video(processed_video, title)
    
    if success:
        log(f"DONE! Publish ID: {info}")
    else:
        log(f"FAILED: {info}")
    
    return success

# ============ ЗАПУСК ============
if __name__ == "__main__":
    # Пример запуска: python auto_bot.py "tiktok_url"
    # Без URL: python auto_bot.py (использует видео из downloads/)
    
    url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if url:
        run_bot(url)
    else:
        # Используем готовое видео из downloads
        ready = get_ready_video()
        if ready:
            print(f"Found: {ready}")
            print("Processing...")
            result = process_video(ready)
            print(f"Result: {result}")
        else:
            print("No videos in downloads/")
            print("Usage: python auto_bot.py <video_url>")