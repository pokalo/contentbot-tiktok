#!/usr/bin/env python3
"""
TikTok Trending Downloader с yt-dlp
Скачивание трендовых и популярных видео с TikTok
"""

import os
import json
import time
import subprocess
from pathlib import Path

DOWNLOADS_FOLDER = "downloads"

def log(msg, level="info"):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level.upper()}] {msg}")


def ensure_folder(name=DOWNLOADS_FOLDER):
    if not os.path.exists(name):
        os.makedirs(name)
    return name


def search_tiktok(query, max_results=10):
    """
    Поиск видео через TikTok
    """
    ensure_folder()
    
    log(f"Searching TikTok for: {query}", "info")
    
    # Используем yt-dlp с куками из браузера
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query} site:tiktok.com",
        "--cookies-from-browser", "chrome",  # Или "firefox", "edge"
        "--print", "%(id)s|%(title)s|%(url)s|%(duration)s|%(view_count)s",
        "--no-download",
        "--no-warnings"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line or '|' not in line:
                continue
            
            parts = line.split('|')
            if len(parts) >= 3:
                videos.append({
                    "id": parts[0].strip(),
                    "title": parts[1].strip()[:100] if len(parts) > 1 else "No title",
                    "url": parts[2].strip() if len(parts) > 2 else "",
                    "duration": parts[3].strip() if len(parts) > 3 else "0",
                    "views": parts[4].strip() if len(parts) > 4 else "0"
                })
        
        log(f"Found {len(videos)} videos", "success")
        return videos
        
    except Exception as e:
        log(f"Search error: {e}", "error")
        return []


def get_trending():
    """Получить текущие тренды (используя популярные хештеги)"""
    hashtags = ["fyp", "viral", "trending", "foryou", "fypシ", "вирусное"]
    all_videos = []
    
    for tag in hashtags:
        log(f"Searching #{tag}...", "info")
        videos = search_tiktok(f"#{tag}", max_results=5)
        for v in videos:
            v["hashtag"] = tag
        all_videos.extend(videos)
        time.sleep(1)
    
    # Убираем дубликаты по URL
    seen = set()
    unique = []
    for v in all_videos:
        if v["url"] not in seen:
            seen.add(v["url"])
            unique.append(v)
    
    log(f"Total unique trending videos: {len(unique)}", "success")
    return unique


def download_video(video_url, filename=None, folder=DOWNLOADS_FOLDER):
    """
    Скачать видео по URL
    
    Returns:
        str: путь к файлу или None
    """
    ensure_folder(folder)
    
    if not filename:
        filename = "%(id)s.%(ext)s"
    
    filepath = os.path.join(folder, filename)
    
    log(f"Downloading: {video_url[:60]}...", "info")
    
    cmd = [
        "yt-dlp",
        "-o", filepath,
        "--no-warnings",
        "--no-progress",
        "--format", "mp4/best",
        video_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Находим скачанный файл
            files = [f for f in os.listdir(folder) if f.endswith('.mp4')]
            if files:
                # Берем последний (обычно самый новый)
                latest = sorted(files, key=lambda x: os.path.getmtime(os.path.join(folder, x)))[-1]
                full_path = os.path.join(folder, latest)
                size = os.path.getsize(full_path)
                log(f"Downloaded: {full_path} ({size / 1024 / 1024:.2f} MB)", "success")
                return full_path
        
        log(f"Download failed: {result.stderr[:200]}", "error")
        return None
        
    except Exception as e:
        log(f"Error: {e}", "error")
        return None


def download_videos_list(videos, folder=DOWNLOADS_FOLDER, max_downloads=5):
    """Скачать список видео"""
    ensure_folder(folder)
    
    downloaded = []
    count = 0
    
    for v in videos:
        if count >= max_downloads:
            break
        
        url = v.get("url")
        if not url:
            continue
        
        path = download_video(url, folder=folder)
        
        if path:
            downloaded.append({
                "path": path,
                "title": v.get("title", ""),
                "id": v.get("id", ""),
                "hashtag": v.get("hashtag", "")
            })
            count += 1
        
        time.sleep(2)
    
    log(f"Downloaded {len(downloaded)} videos", "success")
    return downloaded


# ============ MAIN ============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python tiktok_downloader.py trending [count]")
        print("  python tiktok_downloader.py search <query> [max_results]")
        print("  python tiktok_downloader.py download <url>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "trending":
        videos = get_trending()
        print(json.dumps(videos, indent=2, ensure_ascii=False))
        
    elif command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "fyp"
        max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        videos = search_tiktok(query, max_results)
        print(json.dumps(videos, indent=2, ensure_ascii=False))
        
    elif command == "download":
        url = sys.argv[2] if len(sys.argv) > 2 else ""
        if url:
            path = download_video(url)
            print(f"Downloaded: {path}")
        else:
            print("Please provide URL")
    
    else:
        print(f"Unknown command: {command}")