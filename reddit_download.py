#!/usr/bin/env python3
"""Download trending videos from Reddit"""

import requests
import subprocess
import os
import sys

# Fix Unicode for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DOWNLOADS = "downloads"
DOWNLOADED_FILE = "downloaded_urls.txt"

def is_already_downloaded(url):
    """Check if URL already downloaded"""
    if not os.path.exists(DOWNLOADED_FILE):
        return False
    with open(DOWNLOADED_FILE) as f:
        return url in f.read()

def mark_downloaded(url):
    """Mark URL as downloaded"""
    with open(DOWNLOADED_FILE, "a") as f:
        f.write(url + "\n")

def get_reddit_videos(subreddit="all", limit=25):
    """Get trending videos from subreddit - sort by new to get fresh content"""
    import random
    # Mix hot and new
    sort = random.choice(["hot", "new"])
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Error: {r.status_code}")
        return []

    data = r.json()
    videos = []

    for post in data.get("data", {}).get("children", []):
        p = post.get("data", {})
        url = p.get("url", "")
        
        # Check for video
        if ".mp4" in url or "v.redd.it" in url or "redditvideo" in url:
            videos.append({
                "title": p.get("title", ""),
                "url": url,
                "score": p.get("score", 0),
                "subreddit": p.get("subreddit", ""),
                "author": p.get("author", "")
            })

    return videos

def download_video(url, output_path):
    """Download video using yt-dlp"""
    cmd = ["yt-dlp", "-o", output_path, "-c", "--no-warnings", url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode == 0:
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

DOWNLOADED_FILE = "downloaded_urls.txt"

def is_already_downloaded(url):
    """Check if URL already downloaded"""
    if not os.path.exists(DOWNLOADED_FILE):
        return False
    with open(DOWNLOADED_FILE) as f:
        return url in f.read()

def mark_downloaded(url):
    """Mark URL as downloaded"""
    with open(DOWNLOADED_FILE, "a") as f:
        f.write(url + "\n")

def get_video_from_youtube():
    """Get trending from YouTube Shorts"""
    # Popular Shorts channels
    channels = ["@MrBeast", "@SSSSSSSSSSSSSSSS", "@CBB", "@khaby.lame"]
    
    for channel in channels:
        print(f"Trying YouTube {channel}...")
        try:
            url = f"https://www.youtube.com/{channel}/shorts"
            cmd = ["yt-dlp", "--flat-list", "-c", "--no-warnings", url]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0 and result.stdout:
                print(f"  Found: {channel}")
                return url
        except:
            pass
    return None

def get_reddit_video():
    """Get most trending video from Reddit"""
    print("Getting trending from Reddit...")
    
    # Try multiple subreddits - Russian first
    subreddits = [
        "Pikabu", "Russia", "Russian", "Нарочно",
        "videos", "TikTokCringe", "ReViral", "ContagiousVideos"
    ]
    
    for sub in subreddits:
        print(f"Checking r/{sub}...")
        videos = get_reddit_videos(sub, limit=50)
        
        if not videos:
            continue
            
        # Shuffle to get random video from top
        import random
        random.shuffle(videos)
        
        # Find first video not yet downloaded
        for v in videos:
            url = v['url']
            if is_already_downloaded(url):
                continue
                
            title = v['title'][:50].encode('ascii', 'replace').decode('ascii')
            print(f"\nDownloading: {title}")
            print(f"  Score: {v['score']}")
            
            os.makedirs(DOWNLOADS, exist_ok=True)
            filename = f"{DOWNLOADS}/reddit_{v['score']}.mp4"
            
            if download_video(url, filename):
                mark_downloaded(url)
                print(f"Saved: {filename}")
                return filename
        
        print("  All videos already downloaded, trying next...")
    
    print("No new videos found")
    return None

def get_trending_video():
    """Get trending video from any source"""
    # Try Reddit first
    video = get_reddit_video()
    if video:
        return video
    
    print("No new videos from Reddit")
    return None

if __name__ == "__main__":
    get_reddit_video()