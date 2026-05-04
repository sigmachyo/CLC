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
imgs = re.findall(r'https?://kclc\.ru/wp-content/uploads/[^"\'>\s]+\.(?:jpg|png|jpeg)', html)
links_with_imgs = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>.*?<img[^>]+src="([^"]+)"', html, re.DOTALL)

print("--- Potential Banners ---")
seen_imgs = set()
for link, img in links_with_imgs:
    if "logo" not in img.lower() and "favicon" not in img.lower():
        if img not in seen_imgs:
            print(f"LINK: {link} | IMG: {img}")
            seen_imgs.add(img)

print("\n--- All large images ---")
for img in set(imgs):
    if "logo" not in img.lower() and any(x in img for x in ["1024x", "scaled", "banner"]):
        print(img)
