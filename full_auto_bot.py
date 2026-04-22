#!/usr/bin/env python3
"""Auto Bot - Full cycle: download, process, publish"""

import sys
import os
sys.path.insert(0, ".")

from reddit_download import get_trending_video
from video_processor import trim, add_text
from auto_bot import get_video_duration
from tiktok_api import publish_video

LOG_FILE = "bot_log.txt"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def run_full_cycle():
    """Full automatic cycle"""
    print("=== АВТОБОТ ЗАПУЩЕН ===\n")
    
    # 1. Download trending
    print("[1/4] Скачиваю видео с Reddit...")
    video = get_trending_video()
    if not video:
        print("Не удалось скачать")
        return False
    
    print(f"Скачано: {video}")
    
    # Check duration
    duration = get_video_duration(video)
    print(f"Длительность: {duration:.1f} сек")
    
    # 2. Trim if needed
    if duration > 10:
        print("[2/4] Обрезаю до 10 секунд...")
        video = trim(video, 0, 10)
        print(f"Обрезано: {video}")
    
    # 3. Process (add text)
    print("[3/4] Обрабатываю...")
    result = add_text(video, "#fyp #viral #trending #funny #reddit")
    print(f"Обработано: {result}")
    
    # 4. Publish
    print("[4/4] Публикую...")
    r = publish_video(result, "viral reddit moment #fyp #viral #trending")
    
    if r.get("success"):
        print(f"\n=== ГОТОВО! ===")
        print(f"ID публикации: {r.get('publish_id')}")
        return True
    else:
        print(f"Ошибка: {r.get('error')}")
        return False

if __name__ == "__main__":
    success = run_full_cycle()
    
    # Очистка после успешной публикации
    if success:
        print("\n[Очистка] Удаляю старые видео...")
        os.makedirs("downloads", exist_ok=True)
        os.makedirs("processed", exist_ok=True)
        
        for folder in ["downloads", "processed"]:
            files = []
            for f in os.listdir(folder):
                if f.endswith(".mp4"):
                    path = os.path.join(folder, f)
                    files.append((os.path.getmtime(path), path))
            
            # Удаляем все кроме последних 2х
            files.sort(reverse=True)
            for _, path in files[2:]:
                try:
                    os.remove(path)
                    print(f"  Удалено: {path}")
                except:
                    pass