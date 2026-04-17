#!/usr/bin/env python3
"""Тест публикации видео в TikTok"""

import sys
sys.path.insert(0, r"C:\Users\pav\bot4tiktok")

from tiktok_api import publish_video
import os

video_path = r"C:\Users\pav\bot4tiktok\test_video.mp4"

print(f"Video: {video_path}")
print(f"Size: {os.path.getsize(video_path) / 1024:.1f} KB")
print()

result = publish_video(video_path, "Test video #fyp #testing #api")

print()
print("Result:", "SUCCESS" if result else "FAILED")