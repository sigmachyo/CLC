with open('templates/library/home.html', 'r') as f:
    content = f.read()

# 1. Remove sticky from nav bar
content = content.replace('sticky top-0 z-40 bg-[#0a0f18]/80 backdrop-blur-xl ', '')

# 2. Remove "Папки" from nav bar
import re
content = re.sub(r'<a href="#sec-categories".*?</a>', '', content)

# 3. Add "Все видео" link to Новые видео
video_header_old = '''<div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-white tracking-wide">Новые видео</h2>
            </div>'''
video_header_new = '''<div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-white tracking-wide">Новые видео</h2>
                <a href="#" class="text-white/50 hover:text-white transition-colors text-sm font-medium">Все видео</a>
            </div>'''
content = content.replace(video_header_old, video_header_new)

# 4. Remove Categories block completely
# Find <!-- ПАПКИ И РАЗДЕЛЫ --> and then the very last {% endif %} of that block (which is right before <!-- ДЕТСКИЙ РАЗДЕЛ -->)
start_marker = '<!-- ПАПКИ И РАЗДЕЛЫ -->'
end_marker = '<!-- ДЕТСКИЙ РАЗДЕЛ -->'
start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx:]

with open('templates/library/home.html', 'w') as f:
    f.write(content)
print("Updated library/home.html cleanly")
