#!/usr/bin/env python3
"""
Merge videos from Windows Game Bar captures folder
Handles Russian filenames
"""

import os
import subprocess
import glob
import shutil

CAPTURES_FOLDER = r"C:\Users\pav\Videos\Captures"
OUTPUT_FILE = "merged_output.mp4"
TEMP_FOLDER = "temp_merge"

def get_video_files():
    """Get all MP4 files from captures folder, sorted by name"""
    pattern = os.path.join(CAPTURES_FOLDER, "*.mp4")
    files = glob.glob(pattern)
    return sorted(files, reverse=True)

def merge_videos():
    print("=" * 50)
    print("MERGE VIDEOS - TikTok Demo")
    print("=" * 50)

    files = get_video_files()

    if not files:
        print(f"ERROR: No MP4 files found in {CAPTURES_FOLDER}")
        return

    print(f"\nFound {len(files)} video(s):\n")
    for i, f in enumerate(files, 1):
        filename = os.path.basename(f)
        size_mb = os.path.getsize(f) / 1024 / 1024
        print(f"  {i}. {filename} ({size_mb:.1f} MB)")

    print(f"\nOutput: {OUTPUT_FILE}")
    print("\nPreparing files...")

    temp_dir = TEMP_FOLDER
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    temp_files = []
    for i, file in enumerate(files):
        temp_name = os.path.join(temp_dir, f"video_{i}.mp4")
        shutil.copy2(file, temp_name)
        temp_files.append(temp_name)

    with open("filelist.txt", 'w', encoding='utf-8') as f:
        for file in temp_files:
            f.write(f"file '{file}'\n")

    print("Merging...")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "filelist.txt",
        "-c", "copy",
        OUTPUT_FILE
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            size_mb = os.path.getsize(OUTPUT_FILE) / 1024 / 1024
            print(f"\nSUCCESS! Merged video: {OUTPUT_FILE}")
            print(f"Size: {size_mb:.1f} MB")
        else:
            print(f"\nERROR: {result.stderr}")
    finally:
        if os.path.exists("filelist.txt"):
            os.remove("filelist.txt")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    merge_videos()
