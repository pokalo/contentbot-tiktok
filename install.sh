#!/bin/bash
# Авто-установка Bot4TikTok в Termux одной командой

echo "=== Установка Bot4TikTok ==="

# Установка пакетов
pkg update -y
pkg install python ffmpeg git wget unzip -y

# Создание папки
mkdir -p ~/bot4tiktok
cd ~/bot4tiktok

# Скачивание бота
wget -q https://github.com/pokalo/contentbot-tiktok/archive/refs/heads/master.zip -O bot.zip
unzip -o bot.zip
cd bot4tiktok-master

# Установка зависимостей
pip install requests dotenv yt-dlp 2>/dev/null

# Копирование токена если есть
cp /storage/emulated/0/bot4tiktok/tiktok_token.json . 2>/dev/null

echo "=== ГОТОВО ==="
echo "Запуск: cd ~/bot4tiktok/bot4tiktok-master && python full_auto_bot.py"