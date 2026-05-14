import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\Valera\Desktop\Lesson\6_semestr\Internet\CLC")
sw_path = os.path.join(BASE_DIR, 'static', 'sw.js')
print(f"Checking path: {sw_path}")
print(f"Exists: {os.path.exists(sw_path)}")
