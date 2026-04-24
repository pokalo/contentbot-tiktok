#!/usr/bin/env python3
"""
TikTok Trending Videos Scraper
Сбор трендовых видео для анализа и обработки
"""

import os
import re
import json
import requests
import time
from urllib.parse import quote_plus, urlparse
from tiktok_config import TIKTOK_API_BASE
from tiktok_api import log, get_access_token, load_token

# Папка для сохранения видео
DOWNLOADS_FOLDER = "downloads"


def ensure_folder(name=DOWNLOADS_FOLDER):
    """Создать папку если нет"""
    if not os.path.exists(name):
        os.makedirs(name)
        log(f"Created folder: {name}", "info")
    return name


def search_videos_by_hashtag(hashtag, max_results=20):
    """
    Поиск видео по хештегу через TikTok API
    
    Args:
        hashtag: хештег (без #)
        max_results: максимум видео
    
    Returns:
        list: список видео с информацией
    """
    access_token = get_access_token()
    if not access_token:
        log("No access token", "error")
        return []
    
    # Используем Discovery API для поиска по хештегу
    url = f"{TIKTOK_API_BASE}/discover/v2/hashtag/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Сначала получаем hashtag_id
        r = requests.get(url + f"?hashtag_name={hashtag}", headers=headers)
        
        if r.status_code != 200:
            log(f"Hashtag search failed: {r.status_code} - {r.text}", "error")
            return []
        
        data = r.json()
        hashtag_info = data.get("data", {}).get("hashtags", [])
        
        if not hashtag_info:
            log(f"Hashtag '{hashtag}' not found", "warning")
            return []
        
        hashtag_id = hashtag_info[0].get("id")
        log(f"Found hashtag: {hashtag} (ID: {hashtag_id})", "info")
        
        # Получаем видео этого хештега
        video_url = f"{TIKTOK_API_BASE}/discover/v2/hashtag/video/"
        params = {
            "hashtag_id": hashtag_id,
            "max_count": max_results
        }
        
        r2 = requests.get(video_url, headers=headers, params=params)
        
        if r2.status_code != 200:
            log(f"Video search failed: {r2.status_code}", "error")
            return []
        
        videos_data = r2.json()
        videos = videos_data.get("data", {}).get("videos", [])
        
        result = []
        for v in videos:
            result.append({
                "id": v.get("id"),
                "title": v.get("title", ""),
                "like_count": v.get("like_count", 0),
                "comment_count": v.get("comment_count", 0),
                "share_count": v.get("share_count", 0),
                "view_count": v.get("view_count", 0),
                "duration": v.get("duration", 0),
                "create_time": v.get("create_time", 0),
                "download_url": v.get("download_url", ""),
                "cover_image_url": v.get("cover_image_url", ""),
                "author": v.get("author", {}).get("unique_id", "unknown")
            })
        
        log(f"Found {len(result)} videos for #{hashtag}", "success")
        return result
        
    except Exception as e:
        log(f"Error searching hashtag: {e}", "error")
        return []


def get_user_videos(username, max_results=20):
    """
    Получить видео конкретного пользователя
    
    Args:
        username: имя пользователя
        max_results: максимум видео
    
    Returns:
        list: список видео
    """
    access_token = get_access_token()
    if not access_token:
        return []
    
    url = f"{TIKTOK_API_BASE}/user/info/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Сначала получаем open_id пользователя
    user_info_url = f"{TIKTOK_API_BASE}/user/info/?fields=avatar_url,display_name,follower_count,following_count,likes_count,video_count"
    
    # Это работает только для своего аккаунта
    # Для чужих нужно использовать Display API
    
    log("Getting user videos requires Display API with user targeting", "info")
    return []


def get_feed_videos(max_count=20):
    """
    Получить ленту рекомендаций (FYP)
    
    Args:
        max_count: количество видео
    
    Returns:
        list: список видео из ленты
    """
    access_token = get_access_token()
    if not access_token:
        log("No access token", "error")
        return []
    
    url = f"{TIKTOK_API_BASE}/feed/profile/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "max_count": max_count
    }
    
    try:
        r = requests.get(url, headers=headers, params=params)
        
        if r.status_code != 200:
            log(f"Feed request failed: {r.status_code} - {r.text}", "error")
            return []
        
        data = r.json()
        videos = data.get("data", {}).get("videos", [])
        
        result = []
        for v in videos:
            result.append({
                "id": v.get("id"),
                "title": v.get("title", ""),
                "like_count": v.get("like_count", 0),
                "comment_count": v.get("comment_count", 0),
                "share_count": v.get("share_count", 0),
                "view_count": v.get("view_count", 0),
                "duration": v.get("duration", 0),
                "download_url": v.get("download_url", ""),
                "cover_image_url": v.get("cover_image_url", ""),
                "author": v.get("author", {}).get("unique_id", "unknown")
            })
        
        log(f"Got {len(result)} videos from feed", "success")
        return result
        
    except Exception as e:
        log(f"Error getting feed: {e}", "error")
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
    
    if not filename:
        # Генерируем имя из URL
        parsed = urlparse(video_url)
        # Берем ID из URL или генерируем
        video_id = parsed.path.split('/')[-1] if parsed.path else str(int(time.time()))
        filename = f"video_{video_id}.mp4"
    
    filepath = os.path.join(folder, filename)
    
    log(f"Downloading: {video_url[:50]}...", "info")
    
    try:
        # Пробуем скачать через stream
        r = requests.get(video_url, stream=True, timeout=60)
        
        if r.status_code != 200:
            log(f"Download failed: {r.status_code}", "error")
            return None
        
        # Проверяем тип контента
        content_type = r.headers.get('Content-Type', '')
        if 'video' not in content_type and 'octet-stream' not in content_type:
            log(f"Warning: Content-Type is {content_type}", "warning")
        
        # Сохраняем
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        size = os.path.getsize(filepath)
        log(f"Downloaded: {filepath} ({size / 1024 / 1024:.2f} MB)", "success")
        return filepath
        
    except Exception as e:
        log(f"Download error: {e}", "error")
        return None


def download_videos_list(videos, folder=DOWNLOADS_FOLDER, max_downloads=5):
    """
    Скачать список видео
    
    Args:
        videos: список видео (из search_videos_by_hashtag или get_feed_videos)
        folder: папка для сохранения
        max_downloads: максимум скачиваний
    
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
        
        # Используем ID видео для имени файла
        video_id = v.get("id", str(count))
        filename = f"trending_{video_id}.mp4"
        
        filepath = download_video(url, filename, folder)
        
        if filepath:
            downloaded.append({
                "path": filepath,
                "title": v.get("title", ""),
                "author": v.get("author", ""),
                "like_count": v.get("like_count", 0)
            })
            count += 1
        
        time.sleep(1)  # Пауза между скачиваниями
    
    log(f"Downloaded {len(downloaded)} videos", "success")
    return downloaded


# ============ MAIN ============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python trending_videos.py feed [max_count]")
        print("  python trending_videos.py search <hashtag> [max_results]")
        print("  python trending_videos.py download <video_url>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "feed":
        max_count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        videos = get_feed_videos(max_count)
        print(json.dumps(videos, indent=2, ensure_ascii=False))
        
    elif command == "search":
        hashtag = sys.argv[2] if len(sys.argv) > 2 else "fyp"
        max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        videos = search_videos_by_hashtag(hashtag, max_results)
        print(json.dumps(videos, indent=2, ensure_ascii=False))
        
    elif command == "download":
        url = sys.argv[2] if len(sys.argv) > 2 else ""
        if url:
            path = download_video(url)
            print(f"Downloaded: {path}")
        else:
            print("Please provide video URL")
    
    else:
        print(f"Unknown command: {command}")