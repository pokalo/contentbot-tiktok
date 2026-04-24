import subprocess
import os

os.chdir(r'C:\Users\pav\bot4tiktok')

vf = "drawtext=text='TEST':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-th-50:box=1:boxcolor=black@0.5"

result = subprocess.run(
    ['ffmpeg', '-y', '-i', 'processed/short.mp4', '-vf', vf, '-c:a', 'copy', 'processed/with_text.mp4'],
    capture_output=True,
    timeout=60
)

print('returncode:', result.returncode)
print('exists:', os.path.exists('processed/with_text.mp4'))

if result.returncode != 0:
    print('stderr:', result.stderr[:500])