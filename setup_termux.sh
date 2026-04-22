#!/bin/bash
# Bot4TikTok - Установка в Termux
# Скопируй всё ниже и вставь в Termux

echo "=== Установка Bot4TikTok ==="

# Обновление
pkg update -y

# Установка пакетов
pkg install python ffmpeg git -y

# Создание папки
mkdir -p $HOME/bot4tiktok
cd $HOME/bot4tiktok

# Установка pip пакетов
pip install requests dotenv yt-dlp

# Если есть токен - скачать его
if [ -f "/storage/emulated/0/bot4tiktok/tiktok_token.json" ]; then
    cp /storage/emulated/0/bot4tiktok/tiktok_token.json .
    echo "Токен скопирован!"
fi

echo "=== Готово! ==="
echo "Запуск: cd ~/bot4tiktok && python full_auto_bot.py"