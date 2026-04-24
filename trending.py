#!/usr/bin/env python3
"""
TikTok Trending Videos Scraper (Web Scraping)
Сбор трендовых видео через веб-интерфейс TikTok
"""

import os
import re
import json
import time
import random
from urllib.parse import quote_plus, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
import requests

# Папка для сохранения видео
DOWNLOADS_FOLDER = "downloads"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def log(msg, level="info"):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level.upper()}] {msg}")


def ensure_folder(name=DOWNLOADS_FOLDER):
    """Создать папку если нет"""
    if not os.path.exists(name):
        os.makedirs(name)
    return name


def get_session():
    """Создать сессию с рандомным User-Agent"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    })
    return session


def get_trending_page(page=1, count=10):
    """
    Получить трендовые видео со страницы TikTok
    
    Args:
        page: номер страницы
        count: количество видео
    
    Returns:
        list: список видео
    """
    session = get_session()
    
    url = "https://www.tiktok.com/api/trending/page/feed/"
    params = {
        "aweme_rss": "",
        "page": page,
        "preload_key": "recommend",
        "feed_mode": "for_you",
        "count": count
    }
    
    try:
        r = session.get(url, params=params, timeout=30)
        
        if r.status_code != 200:
            log(f"Request failed: {r.status_code}", "error")
            return []
        
        data = r.json()
        aweme_list = data.get("aweme_list", [])
        
        videos = []
        for aweme in aweme_list:
            video_info = aweme.get("aweme_info", {}).get("aweme_detail", {})
            
            if not video_info:
                # Alternative structure
                video_info = aweme
            
            # Получаем описание
            desc = video_info.get("desc", "")
            
            # Получаем статистику
            stats = video_info.get("statistics", {})
            
            # Получаем автора
            author = video_info.get("author", {})
            
            # Получаем URL видео и изображения
            video_data = video_info.get("video", {})
            download_url = video_data.get("play_addr", {}).get("url", "")
            cover_url = video_data.get("cover", {}).get("url_list", [""])[0]
            
            # Если нет direct URL, пробуем получить через download_addr
            if not download_url:
                download_addr = video_data.get("download_addr", {})
                download_url = download_addr.get("url_list", [""])[0]
            
            videos.append({
                "id": video_info.get("aweme_id", ""),
                "title": desc[:100] if desc else "Без названия",
                "desc": desc,
                "like_count": stats.get("digg_count", 0),
                "comment_count": stats.get("comment_count", 0),
                "share_count": stats.get("share_count", 0),
                "view_count": stats.get("play_count", 0),
                "download_url": download_url,
                "cover_url": cover_url,
                "author_id": author.get("unique_id", ""),
                "author_nickname": author.get("nickname", ""),
                "duration": video_data.get("duration", 0) // 1000 if video_data.get("duration") else 0,
                "create_time": video_info.get("create_time", 0)
            })
        
        log(f"Got {len(videos)} trending videos", "success")
        return videos
        
    except Exception as e:
        log(f"Error getting trending: {e}", "error")
        return []


def search_by_hashtag(hashtag, max_results=20):
    """
    Поиск видео по хештегу
    
    Args:
        hashtag: хештег (без #)
        max_results: максимум результатов
    
    Returns:
        list: список видео
    """
    session = get_session()
    
    # Используем API поиска TikTok
    url = "https://www.tiktok.com/api/search/general/full/"
    params = {
        "keyword": f"#{hashtag}",
        "offset": 0,
        "count": max_results
    }
    
    try:
        r = session.get(url, params=params, timeout=30)
        
        if r.status_code != 200:
            log(f"Search failed: {r.status_code}", "error")
            return []
        
        data = r.json()
        
        # Парсим результаты
        items = data.get("data", [])
        videos = []
        
        for item in items:
            if item.get("type") != 1:  # 1 = video
                continue
            
            video_info = item.get("item", {})
            
            videos.append({
                "id": video_info.get("id", ""),
                "title": video_info.get("desc", "")[:100] if video_info.get("desc") else "Без названия",
                "desc": video_info.get("desc", ""),
                "like_count": video_info.get("stats", {}).get("digg_count", 0),
                "comment_count": video_info.get("stats", {}).get("comment_count", 0),
                "share_count": video_info.get("stats", {}).get("share_count", 0),
                "download_url": video_info.get("video", {}).get("play_addr", {}).get("url", ""),
                "cover_url": video_info.get("video", {}).get("cover", {}).get("url_list", [""])[0],
                "author_id": video_info.get("author", {}).get("unique_id", ""),
                "author_nickname": video_info.get("author", {}).get("nickname", ""),
                "duration": video_info.get("video", {}).get("duration", 0) // 1000
            })
            
            if len(videos) >= max_results:
                break
        
        log(f"Found {len(videos)} videos for #{hashtag}", "success")
        return videos
        
    except Exception as e:
        log(f"Search error: {e}", "error")
        return []


def download_video(video_url, filename=None, folder=DOWNLOADS_FOLDER):
    """
    Скачать видео по URL
    
    Args:
        video_url: ссылка на видео
        filename: имя файла (опционально)
        folder: папка для сохранения
    
    Returns:
        str: путь к файлу или None
    """
    ensure_folder(folder)
    
    session = get_session()
    
    if not filename:
        video_id = str(int(time.time())) + str(random.randint(1000, 9999))
        filename = f"video_{video_id}.mp4"
    
    filepath = os.path.join(folder, filename)
    
    log(f"Downloading: {video_url[:80]}...", "info")
    
    try:
        r = session.get(video_url, stream=True, timeout=120)
        
        if r.status_code != 200:
            log(f"Download failed: {r.status_code}", "error")
            return None
        
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) == 0:  # Log every MB
                            log(f"Progress: {pct:.1f}%", "info")
        
        size = os.path.getsize(filepath)
        log(f"Downloaded: {filepath} ({size / 1024 / 1024:.2f} MB)", "success")
        return filepath
        
    except Exception as e:
        log(f"Download error: {e}", "error")
        if os.path.exists(filepath):
            os.remove(filepath)
        return None


def download_videos_list(videos, folder=DOWNLOADS_FOLDER, max_downloads=5):
    """
    Скачать список видео
    
    Args:
        videos: список видео
        folder: папка
        max_downloads: максимум
    
    Returns:
        list: пути к скачанным файлам
    """
    ensure_folder(folder)
    
    downloaded = []
    count = 0
    
    for v in videos:
        if count >= max_downloads:
            break
        
        url = v.get("download_url")
        if not url:
            continue
        
        video_id = v.get("id", str(count))
        # Очищаем название от спецсимволов
        title = v.get("title", "")[:30]
        title = re.sub(r'[^\w\s-]', '', title).strip()
        
        filename = f"trending_{video_id}_{title}.mp4"
        filename = filename.replace(" ", "_")
        
        filepath = download_video(url, filename, folder)
        
        if filepath:
            downloaded.append({
                "path": filepath,
                "title": v.get("title", ""),
                "author": v.get("author_id", ""),
                "like_count": v.get("like_count", 0),
                "video_id": video_id
            })
            count += 1
        
        time.sleep(2)  # Пауза между скачиваниями
    
    log(f"Total downloaded: {len(downloaded)} videos", "success")
    return downloaded


# ============ MAIN ============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python trending.py trending [count]")
        print("  python trending.py search <hashtag> [max_results]")
        print("  python trending.py download <video_url> [filename]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "trending":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        videos = get_trending_page(count=count)
        print(json.dumps(videos, indent=2, ensure_ascii=False))
        
    elif command == "search":
        hashtag = sys.argv[2] if len(sys.argv) > 2 else "fyp"
        max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        videos = search_by_hashtag(hashtag, max_results)
        print(json.dumps(videos, indent=2, ensure_ascii=False))
        
    elif command == "download":
        url = sys.argv[2] if len(sys.argv) > 2 else ""
        filename = sys.argv[3] if len(sys.argv) > 3 else None
        if url:
            path = download_video(url, filename)
            print(f"Downloaded: {path}")
        else:
            print("Please provide video URL")
    
    else:
        print(f"Unknown command: {command}")