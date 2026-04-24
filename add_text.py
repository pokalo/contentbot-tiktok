import subprocess
import os
import sys

os.chdir(r'C:\Users\pav\bot4tiktok')

video = sys.argv[1] if len(sys.argv) > 1 else 'downloads/7623441894240046356.mp4'
text = sys.argv[2] if len(sys.argv) > 2 else 'TEST'

vf = f"drawtext=text='{text}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-th-50:box=1:boxcolor=black@0.5"
output = f"processed/{os.path.splitext(os.path.basename(video))[0]}_text.mp4"

result = subprocess.run(
    ['ffmpeg', '-y', '-i', video, '-vf', vf, '-c:a', 'copy', output],
    capture_output=True,
    timeout=120
)

if result.returncode == 0 and os.path.exists(output):
    size = os.path.getsize(output)
    print(f"OK: {output} ({size/1024/1024:.2f} MB)")
else:
    print(f"Error: {result.stderr[:200]}")