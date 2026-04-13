import requests
import re
import os
import django
from django.core.files.base import ContentFile
import sys
from urllib.parse import quote, urljoin

# Setup Django
project_path = r'c:\Users\Valera\Desktop\Lesson\6_semestr\Internet\CLC'
if project_path not in sys.path:
    sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kclc.settings')
django.setup()

from church_app.models import HeroBackground

headers = {"User-Agent": "Mozilla/5.0"}
base_url = "https://kclc.ru/"
r = requests.get(base_url, headers=headers)
html = r.text

# Find all links that contain images (potential banners)
# Looking for links to events/news that have a featured image in the uploads
matches = re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>.*?<img[^>]+src="([^"]+)"', html, re.DOTALL)

HeroBackground.objects.all().delete()

count = 0
for m in matches:
    link = m.group(1)
    img_url = m.group(2)
    
    if "logo" in img_url.lower() or "ico" in img_url.lower():
        continue
    if "1024x" not in img_url and "scaled" not in img_url:
        continue
    
    try:
        print(f"Loading {img_url}...")
        # Handle some potential encoding issues in URLs
        # But requests usually handles them if the string is correct
        # The issue before was probably my manual typing.
        
        # Some URLs might be relative?
        if not img_url.startswith("http"):
            img_url = urljoin(base_url, img_url)
            
        img_resp = requests.get(img_url, headers=headers, timeout=10)
        if img_resp.status_code == 200:
            hb = HeroBackground(
                title=f"Banner {count+1}",
                link_url=link,
                is_active=True,
                order=count
            )
            hb.image.save(f"banner_{count}.jpg", ContentFile(img_resp.content), save=False)
            hb.save()
            print(f"Successfully saved banner from {img_url}")
            count += 1
            if count >= 3:
                break
    except Exception as e:
        print(f"Failed {img_url}: {e}")

print(f"Done! Populated {count} banners.")
