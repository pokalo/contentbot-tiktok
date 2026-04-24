import requests

# Тест загрузки напрямую
upload_url = "https://open-upload-sg.tiktokapis.com/upload?upload_id=7630024810399287314&upload_token=abc"

video_path = "processed/7628214166901296404_ai.mp4"

with open(video_path, "rb") as f:
    data = f.read()

headers = {
    "Content-Type": "video/mp4",
    "Content-Length": str(len(data))
}

r = requests.put(upload_url, data=data, headers=headers)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")