import requests
import re
import os

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
try:
    r = requests.get("https://kclc.ru/", headers=headers, timeout=15)
    html = r.text
except Exception as e:
    print(f"Error fetching: {e}")
    exit(1)

# Look for image URLs in the slider/header area
# Often church sites use Revolution Slider (revapi or rs-layer) or similar
# Let's search for large images in wp-content/uploads
imgs = re.findall(r'https?://kclc\.ru/wp-content/uploads/[^"\'>\s]+\.(?:jpg|png|jpeg)', html)

# Also look for links around them
# Patterns like <a href="..."><img src="..."></a>
links_with_imgs = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>.*?<img[^>]+src="([^"]+)"', html, re.DOTALL)

print("--- Potential Banners ---")
seen_imgs = set()
for link, img in links_with_imgs:
    if "logo" not in img.lower() and "favicon" not in img.lowж0er():
        if img not in seen_imgs:
            print(f"LINK: {link} | IMG: {img}")
            seen_imgs.add(img)

print("\n--- All large images ---")
for img in set(imgs):
    if "logo" not in img.lower() and any(x in img for x in ["1024x", "scaled", "banner"]):
        print(img)
