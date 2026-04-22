#!/usr/bin/env python3
"""
AI Video Processor - Обработка видео через ffmpeg
"""

import os
import sys
import subprocess
from pathlib import Path

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def log(msg, level="info"):
    print(f"[{level.upper()}] {msg[:50]}...")


def add_text(video_path, text, output_path=None):
    """Добавить текст с поддержкой кириллицы"""
    if not output_path:
        output_path = f"processed/{Path(video_path).stem}_text.mp4"
    os.makedirs("processed", exist_ok=True)
    
    log(f"Adding: {text}")
    
    # Use Windows font with Cyrillic support
    font = "C:/Windows/Fonts/arial.ttf"
    
    # Encode text to UTF-8 for ffmpeg
    text_encoded = text.encode('utf-8').decode('latin-1')
    
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=36:fontfile={font}:x=(w-text_w)/2:y=h-th-50:box=1:boxcolor=black@0.5",
        "-c:a", "copy", 
        "-paletteuse", 
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        log(f"Saved: {output_path}")
        return output_path
    
    # Try simpler version without fontfile
    cmd2 = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-th-50:box=1:boxcolor=black@0.5",
        "-c:a", "copy",
        output_path
    ]
    result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
    if result2.returncode == 0:
        log(f"Saved: {output_path}")
        return output_path
    
    log(f"Error: {result.stderr[:200]}")
    return None


def change_speed(video_path, speed=1.5, output_path=None):
    """Изменить скорость"""
    if not output_path:
        output_path = f"processed/{Path(video_path).stem}_speed{speed}.mp4"
    os.makedirs("processed", exist_ok=True)
    
    log(f"Speed: {speed}x")
    
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-filter:v", f"setpts={1/speed}*PTS",
        "-filter:a", f"atempo={speed}",
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode == 0:
        log(f"Saved: {output_path}")
        return output_path
    return None


def make_loop(video_path, loops=3, output_path=None):
    """Зациклить"""
    if not output_path:
        output_path = f"processed/{Path(video_path).stem}_loop.mp4"
    os.makedirs("processed", exist_ok=True)
    
    log(f"Loop: {loops}x")
    
    with open("temp_list.txt", "w") as f:
        for _ in range(loops):
            f.write(f"file '{os.path.abspath(video_path)}'\n")
    
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp_list.txt", "-c", "copy", output_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    
    os.remove("temp_list.txt")
    
    if result.returncode == 0:
        log(f"Saved: {output_path}")
        return output_path
    return None


def trim(video_path, start, end, output_path=None):
    """Обрезать"""
    if not output_path:
        output_path = f"processed/{Path(video_path).stem}_trim.mp4"
    os.makedirs("processed", exist_ok=True)
    
    log(f"Trim: {start}-{end}")
    
    cmd = f'ffmpeg -y -ss {start} -i "{video_path}" -t {end-start} -c copy "{output_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        log(f"Saved: {output_path}")
        return output_path
    return None


def add_intro(video_path, text="VIDEO", output_path=None):
    """Добавить заставку"""
    if not output_path:
        output_path = f"processed/{Path(video_path).stem}_intro.mp4"
    os.makedirs("processed", exist_ok=True)
    
    log(f"Intro: {text}")
    
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=720x1280:d=3",
                   "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
                   "-c:v", "libx264", "-t", "3", "-preset", "ultrafast", "temp_intro.mp4"],
                  capture_output=True)
    
    if not os.path.exists("temp_intro.mp4"):
        return None
    
    with open("temp_concat.txt", "w") as f:
        f.write("file 'temp_intro.mp4'\n")
        f.write(f"file '{os.path.abspath(video_path)}'\n")
    
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp_concat.txt", "-c", "copy", output_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    for f in ["temp_intro.mp4", "temp_concat.txt"]:
        if os.path.exists(f): os.remove(f)
    
    if result.returncode == 0:
        log(f"Saved: {output_path}")
        return output_path
    return None


def add_watermark(video_path, text="@username", output_path=None):
    """Водяной знак"""
    if not output_path:
        output_path = f"processed/{Path(video_path).stem}_watermark.mp4"
    os.makedirs("processed", exist_ok=True)
    
    log(f"Watermark: {text}")
    
    cmd = ["ffmpeg", "-y", "-i", video_path,
           "-vf", f"drawtext=text='{text}':fontcolor=white@0.7:fontsize=24:x=w-text_w-10:y=h-text_h-10",
           "-c:a", "copy", output_path]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        log(f"Saved: {output_path}")
        return output_path
    return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python video_processor.py <command> <video> [args]")
        print("Commands: text, speed, loop, trim, intro, watermark")
        sys.exit(1)
    
    cmd, video = sys.argv[1], sys.argv[2]
    
    if cmd == "text":
        result = add_text(video, sys.argv[3] if len(sys.argv) > 3 else "NEW")
    elif cmd == "speed":
        result = change_speed(video, float(sys.argv[3]) if len(sys.argv) > 3 else 1.5)
    elif cmd == "loop":
        result = make_loop(video, int(sys.argv[3]) if len(sys.argv) > 3 else 3)
    elif cmd == "trim":
        result = trim(video, float(sys.argv[3]), float(sys.argv[4]) if len(sys.argv) > 4 else 10)
    elif cmd == "intro":
        result = add_intro(video, sys.argv[3] if len(sys.argv) > 3 else "VIDEO")
    elif cmd == "watermark":
        result = add_watermark(video, sys.argv[3] if len(sys.argv) > 3 else "@username")
    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)
    
    print(f"Result: {result}")