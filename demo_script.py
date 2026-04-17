#!/usr/bin/env python3
"""
Demo Script for TikTok App Review
Автоматически показывает весь процесс публикации видео
"""

import time
from tiktok_api import publish_video, get_video_info, load_token

def run_demo():
    print("=" * 60)
    print("TIKTOK API DEMO - Content Posting Flow")
    print("=" * 60)
    
    print("\n[STEP 1] Checking access token...")
    token = load_token()
    if token:
        print(f"  - Token loaded successfully")
        print(f"  - Open ID: {token.get('open_id', 'N/A')}")
        print(f"  - Scopes: {token.get('scope', 'N/A')}")
    else:
        print("  - ERROR: No token found!")
        print("  - Run: python tiktok_auth.py")
        return
    
    print("\n[STEP 2] Preparing test video...")
    video_path = "test_video.mp4"
    info = get_video_info(video_path)
    if info:
        print(f"  - File: {info['name']}")
        print(f"  - Size: {info['size_mb']} MB")
        print(f"  - Format: {info['format']}")
    else:
        print("  - ERROR: Video file not found!")
        return
    
    print("\n[STEP 3] Initializing video upload...")
    print("  - Connecting to TikTok API...")
    print("  - Validating video parameters...")
    
    print("\n[STEP 4] Publishing video...")
    result = publish_video(
        video_path=video_path,
        title="Demo Video #api #contentposting #tiktok"
    )
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    
    if result['success']:
        print(f"  - Status: SUCCESS")
        print(f"  - Publish ID: {result['publish_id']}")
        print(f"  - Video posted to TikTok successfully!")
    else:
        print(f"  - Status: FAILED")
        print(f"  - Error: {result['error']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    run_demo()
