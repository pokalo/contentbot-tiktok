import subprocess
import os

os.chdir(r'C:\Users\pav\bot4tiktok')

# Большой желтый текст по центру
vf = "drawtext=text='ПРИВЕТ МИР':fontcolor=yellow:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black:boxborderw=10"

result = subprocess.run(
    ['ffmpeg', '-y', '-i', 'downloads/7623441894240046356.mp4', '-vf', vf, '-c:a', 'copy', 'processed/big_text.mp4'],
    capture_output=True,
    timeout=180
)

print('returncode:', result.returncode)
if os.path.exists('processed/big_text.mp4'):
    print('Created:', os.path.getsize('processed/big_text.mp4') / 1024 / 1024, 'MB')
else:
    print('Error')