import subprocess
import os

os.chdir(r'C:\Users\pav\bot4tiktok')

# Ускорим видео в 2 раза - это заметно
result = subprocess.run(
    ['ffmpeg', '-y', '-i', 'downloads/7623441894240046356.mp4', 
     '-filter:v', 'setpts=0.5*PTS', 
     '-filter:a', 'atempo=2',
     '-c:v', 'libx264', '-preset', 'ultrafast',
     '-c:a', 'aac',
     'processed/fast_video.mp4'],
    capture_output=True,
    timeout=300
)

print('returncode:', result.returncode)
if os.path.exists('processed/fast_video.mp4'):
    print('Created:', os.path.getsize('processed/fast_video.mp4') / 1024 / 1024, 'MB')
else:
    print('Error')