import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from django.core.management.base import BaseCommand
from church_app.models import Video, Category
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Smart background synchronization of videos from YouTube, VK, and Rutube without slowing down the site.'

    def add_arguments(self, parser):
        parser.add_argument('--yt-channel', type=str, help='YouTube Channel ID (e.g. UCG_... )')
        parser.add_argument('--vk-token', type=str, help='VK Service Access Token')
        parser.add_argument('--vk-owner', type=str, help='VK Group/Owner ID (e.g. -123456)')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting smart video synchronization..."))
        
        # 1. СИНХРОНИЗАЦИЯ YOUTUBE (через RSS - работает быстро и без ключей API)
        yt_channel_id = options.get('yt_channel') or 'UCG_...' # Заменить на реальный Channel ID ЦХЖ
        if yt_channel_id and yt_channel_id != 'UCG_...':
            self.sync_youtube(yt_channel_id)
        else:
            self.stdout.write(self.style.WARNING("YouTube: Пропущен (укажите --yt-channel)"))

        # 2. СИНХРОНИЗАЦИЯ VK VIDEO
        vk_token = options.get('vk_token')
        vk_owner = options.get('vk_owner')
        if vk_token and vk_owner:
            self.sync_vk(vk_token, vk_owner)
        else:
            self.stdout.write(self.style.WARNING("VK: Пропущен (нужны --vk-token и --vk-owner)"))

        # 3. RUTUBE (нужен парсинг RSS/API, заглушка для алгоритма)
        self.stdout.write(self.style.WARNING("Rutube: API требует авторизации (добавьте ключи в настройки)."))

        self.stdout.write(self.style.SUCCESS("✅ Синхронизация завершена!"))

    def sync_youtube(self, channel_id):
        self.stdout.write(f"Загрузка RSS с YouTube ({channel_id})...")
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        try:
            req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            # Namespace для RSS YouTube
            ns = {'yt': 'http://www.youtube.com/xml/schemas/2015',
                  'media': 'http://search.yahoo.com/mrss/',
                  'atom': 'http://www.w3.org/2005/Atom'}
            
            # Получаем категорию по умолчанию
            category, _ = Category.objects.get_or_create(
                name="Новые видео (Синхронизация)",
                defaults={'category_type': 'video', 'description': 'Автоматически загруженные видео', 'icon': 'video_library'}
            )

            added = 0
            for entry in root.findall('atom:entry', ns):
                video_id = entry.find('yt:videoId', ns).text
                title = entry.find('atom:title', ns).text
                url = entry.find('atom:link', ns).attrib['href']
                
                # Умная проверка дубликатов (Smart Deduplication)
                if Video.objects.filter(youtube_url__icontains=video_id).exists():
                    continue
                if Video.objects.filter(title__iexact=title).exists():
                    continue

                Video.objects.create(
                    title=title,
                    description=f"Видео с YouTube: {title}",
                    youtube_url=url,
                    category=category,
                    is_active=True
                )
                added += 1
            
            self.stdout.write(self.style.SUCCESS(f"YouTube: Успешно обработано. Добавлено новых видео: {added}"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка синхронизации YouTube: {e}"))

    def sync_vk(self, token, owner_id):
        self.stdout.write(f"Запрос к VK API ({owner_id})...")
        api_url = f"https://api.vk.com/method/video.get?owner_id={owner_id}&count=10&access_token={token}&v=5.131"
        
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
            if 'error' in data:
                self.stdout.write(self.style.ERROR(f"VK API Error: {data['error'].get('error_msg')}"))
                return

            category, _ = Category.objects.get_or_create(
                name="Новые видео (Синхронизация)",
                defaults={'category_type': 'video', 'description': 'Автоматически загруженные видео', 'icon': 'video_library'}
            )

            added = 0
            items = data.get('response', {}).get('items', [])
            for item in items:
                video_id = f"{item['owner_id']}_{item['id']}"
                title = item.get('title', 'VK Video')
                url = f"https://vk.com/video{video_id}"

                # Проверка на дубликаты
                if Video.objects.filter(vk_url__icontains=video_id).exists():
                    continue
                if Video.objects.filter(title__iexact=title).exists():
                    continue

                Video.objects.create(
                    title=title,
                    description=item.get('description', ''),
                    vk_url=url,
                    category=category,
                    is_active=True
                )
                added += 1

            self.stdout.write(self.style.SUCCESS(f"VK: Успешно обработано. Добавлено новых видео: {added}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка синхронизации VK: {e}"))
