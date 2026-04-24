#!/usr/bin/env python3
"""
TikTok Video Downloader с прокси поддержкой
"""

import os
import json
import time
import subprocess
import requests
from pathlib import Path

DOWNLOADS_FOLDER = "downloads"

# Настройки прокси (если нужно)
PROXY = None  # "http://user:pass@ip:port" для платных прокси

def log(msg, level="info"):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level.upper()}] {msg}")


def ensure_folder(name=DOWNLOADS_FOLDER):
    if not os.path.exists(name):
        os.makedirs(name)
    return name


def download_video(video_url, filename=None, folder=DOWNLOADS_FOLDER):
    """Скачать видео"""
    ensure_folder(folder)
    
    if not filename:
        filename = "%(title).50s.%(ext)s"
    
    filepath = os.path.join(folder, filename)
    
    log(f"Downloading: {video_url[:60]}...", "info")
    
    cmd = [
        "yt-dlp",
        "-o", filepath,
        "--no-warnings",
        "--format", "mp4/best",
        "--add-header", "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    ]
    
    if PROXY:
        cmd.extend(["--proxy", PROXY])
    
    cmd.append(video_url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Находим скачанный файл
            for f in os.listdir(folder):
                if f.endswith('.mp4') and 'test' not in f.lower():
                    full_path = os.path.join(folder, f)
                    size = os.path.getsize(full_path)
                    log(f"Downloaded: {os.path.basename(full_path)} ({size / 1024 / 1024:.2f} MB)", "success")
                    return full_path
        
        # Если не удалось через yt-dlp, пробуем напрямую
        log(f"yt-dlp failed, trying direct: {result.stderr[:100]}", "warning")
        return download_direct(video_url, folder)
        
    except Exception as e:
        log(f"Error: {e}", "error")
        return None


def download_direct(url, folder=DOWNLOADS_FOLDER):
    """Попытка скачать напрямую через requests"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.tiktok.com/"
    })
    
    try:
        r = session.get(url, stream=True, timeout=60)
        if r.status_code == 200:
            filename = f"video_{int(time.time())}.mp4"
            filepath = os.path.join(folder, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            
            log(f"Downloaded: {filepath}", "success")
            return filepath
    except Exception as e:
        log(f"Direct download failed: {e}", "error")
        return None


def get_video_info(url):
    """Получить информацию о видео без скачивания"""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "id": data.get("id", ""),
                "title": data.get("title", "")[:100],
                "duration": data.get("duration", 0),
                "view_count": data.get("view_count", 0),
                "like_count": data.get("like_count", 0),
                "uploader": data.get("uploader", ""),
                "url": data.get("url", "")
            }
    except Exception as e:
        log(f"Get info error: {e}", "error")
    
    return None


# ============ TEST ============
if __name__ == "__main__":
    import sys
    
    # Тестовое видео
    test_url = "https://www.tiktok.com/@khloekardashian/video/7509903545557695814"
    
    # Попробуем получить инфо
    info = get_video_info(test_url)
    print(json.dumps(info, indent=2, ensure_ascii=False))