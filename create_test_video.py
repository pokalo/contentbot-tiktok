#!/usr/bin/env python3
"""Создание тестового видео для TikTok"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio
import os

# Параметры видео (TikTok формат: 9:16)
width, height = 1080, 1920
duration = 3  # секунд
fps = 24

print("Создание тестового видео...")

frames = []
for i in range(fps * duration):
    # Создаём кадр
    img = Image.new('RGB', (width, height), (30 + i * 5, 30, 60))
    draw = ImageDraw.Draw(img)
    
    # Простой градиент и текст
    t = i / (fps * duration)
    
    # Рисуем прямоугольники для анимации
    y_offset = int(t * 200)
    draw.rectangle([200, 700 + y_offset, 880, 850 + y_offset], fill=(100, 150, 255))
    
    # Пытаемся добавить текст
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    text = f"Test {i+1}/{fps*duration}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) // 2, 900), text, fill=(255, 255, 255), font=font)
    
    frames.append(np.array(img))

# Экспорт
output = os.path.join(os.path.dirname(__file__), "test_video.mp4")
imageio.mimsave(output, frames, fps=fps, codec='libx264')

print(f"\n✅ Видео создано: {output}")
print(f"   Размер: {os.path.getsize(output) / 1024:.1f} KB")