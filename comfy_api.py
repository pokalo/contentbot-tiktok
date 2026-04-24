#!/usr/bin/env python3
"""
ComfyUI API интеграция для бота
Обработка видео через AI
"""

import os
import sys
import time
import json
import requests
import shutil
from pathlib import Path
from datetime import datetime

COMFY_URL = "http://127.0.0.1:8188"
INPUT_FOLDER = "C:/ComfyUI/ComfyUI_windows_portable/ComfyUI/input"
OUTPUT_FOLDER = "C:/ComfyUI/ComfyUI_windows_portable/ComfyUI/output"

def log(msg, level="INFO"):
    print(f"[{level}] {msg}")

def get_comfy_output_files(before_time=0):
    """Получить список новых обработанных файлов"""
    if not os.path.exists(OUTPUT_FOLDER):
        return []
    
    files = []
    for f in os.listdir(OUTPUT_FOLDER):
        if f.endswith(".mp4"):
            fpath = os.path.join(OUTPUT_FOLDER, f)
            mtime = os.path.getmtime(fpath)
            if mtime > before_time:
                files.append((mtime, fpath))
    
    files.sort(reverse=True)
    return [f[1] for f in files]

def upload_video_to_comfy(video_path):
    """Загрузить видео в ComfyUI через API"""
    filename = os.path.basename(video_path)
    dest = os.path.join(INPUT_FOLDER, filename)
    
    shutil.copy2(video_path, dest)
    log(f"Uploaded: {filename}")
    return filename

def create_workflow_video_enhance(input_filename, output_filename, model="General Restore Model (1x)", resolution="720p"):
    """Создать workflow для улучшения видео через Topaz Video Enhance"""
    
    workflow = {
        "3": {
            "inputs": {
                "file": input_filename
            },
            "class_type": "LoadVideo",
            "_meta": {"title": "Load Video"}
        },
        "4": {
            "inputs": {
                "video": ["3", 0],
                "upscaler_enabled": True,
                "upscaler_model": "Starlight (Astra) Fast",
                "upscaler_resolution": "FullHD (1080p)"
            },
            "class_type": "TopazVideoEnhance",
            "_meta": {"title": "Topaz Video Enhance"}
        },
        "5": {
            "inputs": {
                "video": ["4", 0],
                "filename_prefix": "ComfyUI",
                "format": "mp4",
                "codec": "h264"
            },
            "class_type": "SaveVideo",
            "_meta": {"title": "Save Video"}
        }
    }
    
    return workflow

def queue_prompt(workflow):
    """Отправить задачу на выполнение"""
    url = f"{COMFY_URL}/prompt"
    
    response = requests.post(url, json={"prompt": workflow})
    
    if response.status_code == 200:
        result = response.json()
        prompt_id = result.get("prompt_id")
        log(f"Queued: {prompt_id}")
        return prompt_id
    else:
        log(f"Queue error: {response.status_code} - {response.text}", "ERROR")
        return None

def get_history(prompt_id):
    """Получить историю выполнения"""
    url = f"{COMFY_URL}/history/{prompt_id}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log(f"History error: {e}", "ERROR")
    
    return None

def wait_for_completion(prompt_id, timeout=600):
    """Ждать завершения обработки (долго для видео)"""
    log(f"Waiting for completion (timeout: {timeout}s)...")
    
    start = time.time()
    last_status = None
    
    while time.time() - start < timeout:
        history = get_history(prompt_id)
        
        if history and prompt_id in history:
            status = history[prompt_id].get("status", {})
            
            if status.get("completed"):
                log("✓ Complete!")
                return True
            
            if status.get("errored"):
                err_msg = status.get("exception_message", "Unknown error")
                log(f"✗ Error: {err_msg}", "ERROR")
                return False
            
            new_status = status.get("status_str", "")
            if new_status != last_status:
                log(f"Status: {new_status}")
                last_status = new_status
        
        time.sleep(10)
    
    log("Timeout!", "ERROR")
    return False

def get_latest_output():
    """Получить последний обработанный файл"""
    files = get_comfy_output_files()
    return files[0] if files else None

def process_video_ai(input_video, effect="enhance", model="General Restore Model (1x)", resolution="720p"):
    """
    Обработать видео через ComfyUI AI
    
    Args:
        input_video: путь к входному видео
        effect: "enhance" - улучшение качества
        model: модель HitPaw
        resolution: целевое разрешение
    
    Returns:
        путь к обработанному видео или None
    """
    log(f"Processing: {input_video}")
    
    if effect == "enhance":
        return process_with_hitpaw(input_video, model, resolution)
    
    log(f"Unknown effect: {effect}", "ERROR")
    return None

def process_with_hitpaw(input_video, model, resolution):
    """Обработка через Topaz Video Enhance API"""
    
    input_filename = upload_video_to_comfy(input_video)
    output_filename = f"enhanced_{int(time.time())}.mp4"
    
    workflow = create_workflow_video_enhance(input_filename, output_filename, model, resolution)
    
    prompt_id = queue_prompt(workflow)
    if not prompt_id:
        return None
    
    if not wait_for_completion(prompt_id, timeout=600):
        return None
    
    result_file = get_latest_output()
    if result_file:
        log(f"Result: {result_file}")
        return result_file
    
    log("No output file found", "ERROR")
    return None

def check_comfy_status():
    """Проверить статус ComfyUI"""
    try:
        r = requests.get(f"{COMFY_URL}/system_stats", timeout=5)
        if r.status_code == 200:
            stats = r.json()
            print(f"ComfyUI: OK")
            print(f"VRAM: {stats.get('vram_used', '?')}/{stats.get('vram_total', '?')} MB")
            print(f"RAM: {stats.get('ram_used', '?')}/{stats.get('ram_total', '?')} MB")
            return True
    except Exception as e:
        print(f"ComfyUI not responding: {e}")
    return False

if __name__ == "__main__":
    check_comfy_status()