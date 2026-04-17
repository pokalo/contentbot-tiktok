# TikTok Bot - Auto Publisher

Автоматическая публикация видео в TikTok через Content Posting API.

## Структура

```
bot4tiktok/
├── tiktok_config.py    # Конфигурация (API ключи из .env)
├── tiktok_auth.py      # OAuth авторизация (PKCE)
├── tiktok_api.py       # Публикация видео
├── callback_server.py  # Локальный сервер для OAuth callback
├── .env                 # Credentials (НЕ в git!)
├── .env.example         # Шаблон для .env
├── .gitignore           # Исключения для git
└── requirements.txt     # Зависимости Python
```

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка credentials

```bash
# Скопируй пример
cp .env.example .env

# Отредактируй .env, вставив свои ключи из TikTok Developer Portal
```

### 3. Авторизация

```bash
python tiktok_auth.py
```

Откроется браузер для авторизации TikTok. После одобрения:
- URL перенаправит на callback с параметром `code`
- Скопируй `code` из URL
- Вставь в терминал

Токен сохранится в `tiktok_token.json`.

### 4. Проверка токена

```bash
python tiktok_api.py
```

Покажет статус токена и время до истечения.

### 5. Публикация видео

```python
from tiktok_api import publish_video

result = publish_video("video.mp4", "My video #fyp #viral")

if result["success"]:
    print(f"Published! ID: {result['publish_id']}")
else:
    print(f"Error: {result['error']}")
```

## Переменные окружения (.env)

```
TIKTOK_CLIENT_KEY=your_client_key_here
TIKTOK_CLIENT_SECRET=your_client_secret_here
TIKTOK_REDIRECT_URI=http://localhost:8080/callback  # опционально
```

## Как работает

1. **OAuth PKCE** — безопасная авторизация без раскрытия client_secret
2. **Auto-refresh** — токен обновляется автоматически перед истечением
3. **S3 Upload** — видео загружается на S3 через presigned URL от TikTok
4. **Status polling** — проверка статуса публикации

## Токен

Токен живёт 24 часа. Refresh token — год.

Автообновление происходит автоматически при вызове `get_access_token()`.

## Валидация видео

Перед загрузкой автоматически проверяется:
- Формат файла (.mp4, .mov, .avi, .mkv)
- Размер (< 500MB)
- Целостность файла (не пустой, не битый)

## Возможные проблемы

### "Missing credentials"
Создай `.env` файл с `TIKTOK_CLIENT_KEY` и `TIKTOK_CLIENT_SECRET`.

### "Invalid code_verifier"
PKCE требует точного совпадения code_verifier. Используй `tiktok_auth.py`.

### "Upload failed"
Проверь:
- Формат видео (MP4, H.264)
- Размер (< 500MB)
- Права в Developer Portal (Content Posting API включён)

### "Token expired"
Запусти `python tiktok_api.py` — он попробует refresh. Если не вышло — авторизуйся заново.

## TODO

- [ ] Автогенерация видео
- [ ] Планировщик постов
- [ ] Массовая загрузка
- [ ] Аналитика публикаций