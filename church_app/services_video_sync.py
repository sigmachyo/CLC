import re
import urllib.request
import json
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timezone as dt_timezone
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils.text import slugify
from church_app.models import Video, Category

CHURCH_CHANNEL_ID = 'UCgroLbpNBJ4f1CDiF6HLWJw'   # @kclcfamily
WORSHIP_CHANNEL_ID = 'UC1guJphYzzOOUq5ddQQe0Ig'  # @kclcworship
RUTUBE_CHANNEL_ID = '39733690'
VK_GROUP_ID = '7917420'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
}

RUS_MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
    'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'июн': 6,
    'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12,
}


def parse_date_from_text(title: str):
    """Извлекает дату проведения служения из русского заголовка видео"""
    if not title:
        return None
    # 1. Формат "20 сентября 2026" или "20 сентября"
    m = re.search(r'\b(\d{1,2})\s+([а-яё]+)\s*(\d{4})?\b', title.lower())
    if m:
        day = int(m.group(1))
        month_str = m.group(2)
        year = int(m.group(3)) if m.group(3) else 2026
        month = RUS_MONTHS.get(month_str)
        if month and 1 <= day <= 31:
            try:
                return datetime(year, month, day, 11, 0, tzinfo=dt_timezone.utc)
            except ValueError:
                pass

    # 2. Формат "30.08.2026" или "23/08/2026"
    m2 = re.search(r'\b(\d{1,2})[\./](\d{1,2})[\./](\d{4})\b', title)
    if m2:
        day, month, year = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            try:
                return datetime(year, month, day, 11, 0, tzinfo=dt_timezone.utc)
            except ValueError:
                pass
    return None


def normalize_title(text: str) -> str:
    """Нормализует заголовок для точного сравнения и поиска дубликатов"""
    if not text:
        return ""
    cleaned = text.lower()
    cleaned = re.sub(r'/\s*цхж\s*красноярск', '', cleaned)
    cleaned = re.sub(r'\|\s*цхж\s*красноярск', '', cleaned)
    cleaned = re.sub(r'цхж\s*красноярск', '', cleaned)
    cleaned = re.sub(r'прямой\s*эфир\s*\|', '', cleaned)
    cleaned = re.sub(r'онлайн\s*трансляция', '', cleaned)
    cleaned = re.sub(r'[«»""\'\(\)\[\]\|/\\_\-–—\.,:;!?]', ' ', cleaned)
    words = [w.strip() for w in cleaned.split() if len(w.strip()) > 1]
    return " ".join(words)


def are_titles_similar(t1: str, t2: str) -> bool:
    """Проверяет похожесть названий с YouTube, RuTube и VK для исключения дублей"""
    norm1 = normalize_title(t1)
    norm2 = normalize_title(t2)
    if not norm1 or not norm2:
        return False
    if norm1 == norm2:
        return True

    words1 = set(norm1.split())
    words2 = set(norm2.split())

    date_pattern = r'\b(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)|\d{2}\s*\d{2}\s*\d{4})\b'
    m1 = re.findall(date_pattern, norm1)
    m2 = re.findall(date_pattern, norm2)
    if m1 and m2 and m1[0] == m2[0] and ('служение' in norm1 or 'служение' in norm2 or 'наделение' in norm1 or 'наделение' in norm2):
        return True

    intersection = words1.intersection(words2)
    smaller = min(len(words1), len(words2))
    overlap = len(intersection) / smaller if smaller > 0 else 0

    return overlap >= 0.65


def parse_time_to_seconds(time_str: str) -> int:
    """Конвертирует строку '2:13:35' или '35:20' в секунды"""
    if not time_str:
        return 0
    parts = time_str.strip().split(':')
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, TypeError):
        pass
    return 0


def get_or_create_categories():
    """Создает базовые рубрики видео, если их еще нет"""
    cats = {
        'propovedi': ('Проповеди', 'fa-book-open', 1),
        'voskresnye-sluzheniya': ('Воскресные служения', 'fa-church', 2),
        'konferencii': ('Конференции', 'fa-microphone-lines', 3),
        'proslavlenie': ('Прославление', 'fa-music', 4),
    }
    result = {}
    for slug, (name, icon, order) in cats.items():
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            category_type='video',
            defaults={'name': name, 'icon': icon, 'order': order, 'is_active': True}
        )
        result[slug] = cat
    return result


def detect_category(title: str, categories_dict: dict, is_worship: bool = False) -> Category:
    """Автоматически определяет категорию по ключевым словам и источнику"""
    if is_worship:
        return categories_dict.get('proslavlenie') or list(categories_dict.values())[0]

    t = title.lower()
    if any(k in t for k in ['хвала', 'поклонение', 'прославлен', 'песн', 'клип', 'worship', 'cover', 'all my oil', 'yeshua', 'яхве']):
        return categories_dict.get('proslavlenie') or list(categories_dict.values())[0]
    if any(k in t for k in ['конференция', 'семинар', 'школа', 'тренинг', 'два источника', 'звуки небес', 'альфа']):
        return categories_dict.get('konferencii') or list(categories_dict.values())[0]
    if any(k in t for k in ['воскресное служение', 'служение', 'трансляция', 'воскресенье', 'наделение']):
        return categories_dict.get('voskresnye-sluzheniya') or list(categories_dict.values())[0]
    return categories_dict.get('propovedi') or list(categories_dict.values())[0]


def fetch_youtube_feed(channel_id: str, is_worship: bool = False):
    """Получает до 15 свежих видео с официального YouTube Atom RSS фида с точной датой и просмотрами"""
    videos = []
    url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        res = urllib.request.urlopen(req, timeout=10)
        content = res.read()
        root = ET.fromstring(content)
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/'
        }
        for entry in root.findall('atom:entry', ns):
            title_elem = entry.find('atom:title', ns)
            link_elem = entry.find('atom:link', ns)
            video_id_elem = entry.find('yt:videoId', ns)
            desc_elem = entry.find('media:group/media:description', ns)
            thumb_elem = entry.find('media:group/media:thumbnail', ns)
            pub_elem = entry.find('atom:published', ns)
            views_elem = entry.find('media:group/media:community/media:statistics', ns)

            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''
            video_id = video_id_elem.text.strip() if video_id_elem is not None and video_id_elem.text else ''
            link = link_elem.attrib.get('href') if link_elem is not None else (f'https://www.youtube.com/watch?v={video_id}' if video_id else '')
            desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ''
            thumb = thumb_elem.attrib.get('url') if thumb_elem is not None else (f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg' if video_id else '')

            published_at = None
            if pub_elem is not None and pub_elem.text:
                try:
                    published_at = datetime.fromisoformat(pub_elem.text.strip())
                except Exception:
                    pass

            if not published_at:
                published_at = parse_date_from_text(title)

            views_count = 0
            if views_elem is not None and views_elem.attrib.get('views'):
                try:
                    views_count = int(views_elem.attrib.get('views'))
                except Exception:
                    pass

            if video_id and title:
                videos.append({
                    'source': 'youtube',
                    'video_id': video_id,
                    'title': title,
                    'description': desc,
                    'youtube_url': link,
                    'rutube_url': None,
                    'vk_url': None,
                    'duration': 0,
                    'views_count': views_count,
                    'published_at': published_at,
                    'thumbnail_url': thumb,
                    'is_worship': is_worship,
                })
    except Exception as e:
        print(f"Error fetching YouTube feed for {channel_id}: {e}")
    return videos


def fetch_youtube_html(url: str, is_worship: bool = False):
    """Парсит YouTube страницу (/videos или /streams) и извлекает lockupViewModel / videoRenderer"""
    videos = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        html = urllib.request.urlopen(req, timeout=12).read().decode('utf-8', errors='ignore')
        m = re.search(r'var ytInitialData = ({.*?});</script>', html)
        if not m:
            m = re.search(r'window\[\"ytInitialData\"\] = ({.*?});</script>', html)
        if not m:
            return videos

        data = json.loads(m.group(1))

        def search_items(obj):
            if isinstance(obj, dict):
                # Формат modern YouTube: lockupViewModel
                if 'lockupViewModel' in obj:
                    lvm = obj['lockupViewModel']
                    content_id = lvm.get('contentId')
                    meta = lvm.get('metadata', {}).get('lockupMetadataViewModel', {})
                    title = meta.get('title', {}).get('content', '').strip()
                    thumb_data = lvm.get('contentImage', {}).get('thumbnailViewModel', {}).get('image', {}).get('sources', [])
                    thumb = thumb_data[-1].get('url') if thumb_data else (f'https://i.ytimg.com/vi/{content_id}/hqdefault.jpg' if content_id else '')
                    
                    # Извлечение длительности из оверлея бейджа
                    duration_sec = 0
                    badges = lvm.get('contentImage', {}).get('thumbnailViewModel', {}).get('overlays', [])
                    for b in badges:
                        b_text = b.get('thumbnailBottomOverlayViewModel', {}).get('badges', [{}])[0].get('thumbnailBadgeViewModel', {}).get('text', '')
                        if b_text and ':' in b_text:
                            duration_sec = parse_time_to_seconds(b_text)
                            break

                    pub_date = parse_date_from_text(title)

                    if content_id and title:
                        videos.append({
                            'source': 'youtube',
                            'video_id': content_id,
                            'title': title,
                            'description': '',
                            'youtube_url': f'https://www.youtube.com/watch?v={content_id}',
                            'rutube_url': None,
                            'vk_url': None,
                            'duration': duration_sec,
                            'views_count': 0,
                            'published_at': pub_date,
                            'thumbnail_url': thumb,
                            'is_worship': is_worship,
                        })
                # Формат legacy/fallback: videoRenderer
                elif 'videoRenderer' in obj:
                    vr = obj['videoRenderer']
                    vid = vr.get('videoId')
                    title_runs = vr.get('title', {}).get('runs', [])
                    title = title_runs[0].get('text', '').strip() if title_runs else vr.get('title', {}).get('simpleText', '').strip()
                    thumbs = vr.get('thumbnail', {}).get('thumbnails', [])
                    thumb = thumbs[-1].get('url') if thumbs else (f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg' if vid else '')
                    dur_str = vr.get('lengthText', {}).get('simpleText', '')
                    duration_sec = parse_time_to_seconds(dur_str) if dur_str else 0
                    
                    # Просмотры
                    views_count = 0
                    view_str = vr.get('viewCountText', {}).get('simpleText', '')
                    if view_str:
                        m_v = re.search(r'([\d\s]+)', view_str.replace('\xa0', ' '))
                        if m_v:
                            try:
                                views_count = int(m_v.group(1).replace(' ', ''))
                            except Exception:
                                pass

                    pub_date = parse_date_from_text(title)

                    if vid and title:
                        videos.append({
                            'source': 'youtube',
                            'video_id': vid,
                            'title': title,
                            'description': '',
                            'youtube_url': f'https://www.youtube.com/watch?v={vid}',
                            'rutube_url': None,
                            'vk_url': None,
                            'duration': duration_sec,
                            'views_count': views_count,
                            'published_at': pub_date,
                            'thumbnail_url': thumb,
                            'is_worship': is_worship,
                        })
                for k, v in obj.items():
                    search_items(v)
            elif isinstance(obj, list):
                for it in obj:
                    search_items(it)

        search_items(data)
    except Exception as e:
        print(f"Error fetching YouTube HTML from {url}: {e}")

    # Дедупликация по video_id
    seen = set()
    dedup = []
    for v in videos:
        if v['video_id'] not in seen:
            seen.add(v['video_id'])
            dedup.append(v)
    return dedup


def fetch_all_youtube_videos():
    """
    Загружает полный каталог видео с YouTube:
    1. Канал церкви @kclcfamily (Atom feed + /videos + /streams)
    2. Канал прославления @kclcworship (Atom feed + /videos)
    """
    all_yt = []
    seen_ids = set()

    def add_items(items):
        for it in items:
            vid = it.get('video_id')
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                all_yt.append(it)
            elif vid and vid in seen_ids:
                for ex in all_yt:
                    if ex.get('video_id') == vid:
                        if not ex.get('description') and it.get('description'):
                            ex['description'] = it['description']
                        if not ex.get('published_at') and it.get('published_at'):
                            ex['published_at'] = it['published_at']
                        if not ex.get('views_count') and it.get('views_count'):
                            ex['views_count'] = it['views_count']
                        if not ex.get('duration') and it.get('duration'):
                            ex['duration'] = it['duration']
                        break

    print("Fetching Church YouTube RSS...")
    add_items(fetch_youtube_feed(CHURCH_CHANNEL_ID, is_worship=False))

    print("Fetching Church YouTube Videos HTML...")
    add_items(fetch_youtube_html('https://www.youtube.com/@kclcfamily/videos', is_worship=False))

    print("Fetching Church YouTube Streams HTML...")
    add_items(fetch_youtube_html('https://www.youtube.com/@kclcfamily/streams', is_worship=False))

    print("Fetching Worship YouTube RSS...")
    add_items(fetch_youtube_feed(WORSHIP_CHANNEL_ID, is_worship=True))

    print("Fetching Worship YouTube Videos HTML (@kclcworship)...")
    add_items(fetch_youtube_html('https://www.youtube.com/@kclcworship/videos', is_worship=True))

    print(f"Total YouTube videos collected: {len(all_yt)}")
    return all_yt


def fetch_rutube_videos():
    """Получает актуальные видео с RuTube API канала церкви с точной датой и просмотрами"""
    videos = []
    for page in [1, 2]:
        url = f'https://rutube.ru/api/video/person/{RUTUBE_CHANNEL_ID}/?page={page}'
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            res = urllib.request.urlopen(req, timeout=10)
            data = json.loads(res.read().decode('utf-8'))
            results = data.get('results', [])
            if not results:
                break
            for item in results:
                v_url = item.get('video_url') or f"https://rutube.ru/video/{item.get('id')}/"
                thumb = item.get('thumbnail_url') or (item.get('picture_url') if isinstance(item.get('picture_url'), str) else None)
                
                pub_str = item.get('publication_ts') or item.get('created_ts')
                published_at = None
                if pub_str:
                    try:
                        published_at = datetime.fromisoformat(pub_str).replace(tzinfo=dt_timezone.utc)
                    except Exception:
                        pass

                views_count = 0
                if item.get('hits'):
                    try:
                        views_count = int(item.get('hits'))
                    except Exception:
                        pass

                videos.append({
                    'source': 'rutube',
                    'title': item.get('title', '').strip(),
                    'description': item.get('description', '').strip(),
                    'rutube_url': v_url,
                    'youtube_url': None,
                    'vk_url': None,
                    'duration': item.get('duration', 0),
                    'views_count': views_count,
                    'published_at': published_at,
                    'thumbnail_url': thumb,
                })
        except Exception as e:
            print(f"Error fetching RuTube page {page}: {e}")
            break
    return videos


def fetch_vk_videos():
    """Получает актуальные видеозаписи и прямые эфиры с сообщества VK https://vk.ru/kclcfamily"""
    videos = []
    url = f"https://vk.com/widget_community.php?gid={VK_GROUP_ID}&mode=4"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        res = urllib.request.urlopen(req, timeout=10)
        html = res.read().decode("windows-1251", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        posts = soup.find_all("div", class_="wall_post_cont")
        for p in posts:
            video_a = p.find("a", href=lambda h: h and "video" in h)
            if not video_a:
                continue

            v_href = video_a["href"]
            m = re.search(r'video(-?\d+_\d+)', v_href)
            if not m:
                continue
            raw_vid = m.group(1)
            vk_url = f"https://vk.com/video{raw_vid}"

            dur_str = video_a.get_text(strip=True)
            duration_sec = parse_time_to_seconds(dur_str)

            text_div = p.find("div", class_="wall_post_text")
            full_text = text_div.get_text(separator="\n", strip=True) if text_div else ""
            lines = [l.strip() for l in full_text.split("\n") if l.strip()]
            title = lines[0] if lines else "Служение KCLC (VK Video)"
            desc = "\n".join(lines[1:]) if len(lines) > 1 else ""

            img_elem = video_a.find("img")
            thumb_url = img_elem.get("src") if img_elem else ""

            pub_date = parse_date_from_text(title)

            videos.append({
                'source': 'vk',
                'title': title,
                'description': desc,
                'vk_url': vk_url,
                'youtube_url': None,
                'rutube_url': None,
                'duration': duration_sec,
                'views_count': 0,
                'published_at': pub_date,
                'thumbnail_url': thumb_url,
            })
    except Exception as e:
        print(f"Error fetching VK videos: {e}")
    return videos


def download_thumbnail(thumbnail_url: str):
    """Скачивает легкое изображение обложки (постер) для локального кэша"""
    if not thumbnail_url:
        return None
    try:
        req = urllib.request.Request(thumbnail_url, headers=HEADERS)
        data = urllib.request.urlopen(req, timeout=6).read()
        return data
    except Exception as e:
        return None


def sync_videos():
    """
    Синхронизация видео:
    1. Главный приоритет — YouTube (каналы @kclcfamily и @kclcworship).
    2. Все видео из YouTube берутся как основа.
    3. К ним привязываются RuTube и VK как резервные (fallback) ссылки для плеера.
    4. Точные даты публикации (published_at) и просмотры (views_count) извлекаются и обновляются.
    5. Песни прославления (@kclcworship) автоматически маркируются рубрикой 'proslavlenie'.
    """
    categories = get_or_create_categories()

    print("Fetching YouTube videos (@kclcfamily and @kclcworship)...")
    youtube_items = fetch_all_youtube_videos()

    print("Fetching RuTube videos...")
    rutube_items = fetch_rutube_videos()
    print(f"Found {len(rutube_items)} RuTube videos.")

    print("Fetching VK videos (kclcfamily)...")
    vk_items = fetch_vk_videos()
    print(f"Found {len(vk_items)} VK videos.")

    unified_videos = []

    # 1. ОСНОВА: Сначала добавляем ВСЕ YouTube видео (приоритет №1)
    for y in youtube_items:
        pub = parse_date_from_text(y['title']) or y.get('published_at')
        unified_videos.append({
            'title': y['title'],
            'description': y.get('description', ''),
            'youtube_url': y['youtube_url'],
            'rutube_url': None,
            'vk_url': None,
            'duration': y.get('duration', 0),
            'views_count': y.get('views_count', 0),
            'published_at': pub,
            'thumbnail_url': y.get('thumbnail_url'),
            'is_worship': y.get('is_worship', False),
            'sources': ['youtube']
        })

    # 2. Привязываем RuTube к совпадающим YouTube видео (или добавляем как запасные)
    merged_rt = 0
    for r in rutube_items:
        r_title = r['title']
        r_url = r['rutube_url']
        r_views = r.get('views_count', 0)
        r_pub = parse_date_from_text(r_title) or r.get('published_at')
        matched = False
        for u in unified_videos:
            if are_titles_similar(u['title'], r_title):
                u['rutube_url'] = r_url
                u['sources'].append('rutube')
                if not u['description'] and r.get('description'):
                    u['description'] = r['description']
                if not u['duration'] and r.get('duration'):
                    u['duration'] = r['duration']
                if r_pub and (not u.get('published_at') or parse_date_from_text(r_title)):
                    u['published_at'] = r_pub
                if r_views > u.get('views_count', 0):
                    u['views_count'] = r_views
                matched = True
                merged_rt += 1
                break
        if not matched:
            unified_videos.append({
                'title': r_title,
                'description': r.get('description', ''),
                'youtube_url': None,
                'rutube_url': r_url,
                'vk_url': None,
                'duration': r.get('duration', 0),
                'views_count': r_views,
                'published_at': r_pub,
                'thumbnail_url': r.get('thumbnail_url'),
                'is_worship': False,
                'sources': ['rutube']
            })

    # 3. Привязываем VK к совпадающим видео
    merged_vk = 0
    for v in vk_items:
        v_title = v['title']
        v_url = v['vk_url']
        v_pub = parse_date_from_text(v_title) or v.get('published_at')
        matched = False
        for u in unified_videos:
            if are_titles_similar(u['title'], v_title):
                u['vk_url'] = v_url
                u['sources'].append('vk')
                if not u['duration'] and v.get('duration'):
                    u['duration'] = v['duration']
                if v_pub and not u.get('published_at'):
                    u['published_at'] = v_pub
                matched = True
                merged_vk += 1
                break
        if not matched:
            unified_videos.append({
                'title': v_title,
                'description': v.get('description', ''),
                'youtube_url': None,
                'rutube_url': None,
                'vk_url': v_url,
                'duration': v.get('duration', 0),
                'views_count': 0,
                'published_at': v_pub,
                'thumbnail_url': v.get('thumbnail_url'),
                'is_worship': False,
                'sources': ['vk']
            })

    print(f"Merge summary: {merged_rt} RuTube & {merged_vk} VK fallbacks matched to YouTube videos. Total unified items: {len(unified_videos)}")

    saved_count = 0
    updated_count = 0

    for idx, item in enumerate(unified_videos):
        title = item['title']
        yt_url = item['youtube_url']
        rt_url = item['rutube_url']
        vk_url = item['vk_url']
        is_worship = item.get('is_worship', False)
        pub_date = parse_date_from_text(title) or item.get('published_at')
        views = item.get('views_count', 0)

        existing = None
        if yt_url:
            existing = Video.objects.filter(youtube_url=yt_url).first()
        if not existing and rt_url:
            existing = Video.objects.filter(rutube_url=rt_url).first()
        if not existing and vk_url:
            existing = Video.objects.filter(vk_url=vk_url).first()
        if not existing:
            for v in Video.objects.all():
                if are_titles_similar(v.title, title):
                    existing = v
                    break

        cat = detect_category(title, categories, is_worship=is_worship)

        if existing:
            changed = False
            if yt_url and existing.youtube_url != yt_url:
                existing.youtube_url = yt_url
                changed = True
            if rt_url and not existing.rutube_url:
                existing.rutube_url = rt_url
                changed = True
            if vk_url and not existing.vk_url:
                existing.vk_url = vk_url
                changed = True
            if is_worship and existing.category != categories['proslavlenie']:
                existing.category = categories['proslavlenie']
                changed = True
            if item.get('duration') and not existing.duration:
                existing.duration = item['duration']
                changed = True
            if not existing.description and item.get('description'):
                existing.description = item['description']
                changed = True
            if pub_date and (not existing.published_at or existing.published_at != pub_date):
                existing.published_at = pub_date
                changed = True
            if views > existing.views_count:
                existing.views_count = views
                changed = True
            if changed:
                existing.save()
                updated_count += 1
        else:
            new_video = Video(
                title=title[:200],
                description=item.get('description', ''),
                category=cat,
                youtube_url=yt_url,
                rutube_url=rt_url,
                vk_url=vk_url,
                duration=item.get('duration', 0),
                views_count=views,
                published_at=pub_date,
                is_active=True,
                is_featured=(idx < 3),
                order=idx,
                video_file=None
            )
            new_video.save()

            thumb_data = download_thumbnail(item.get('thumbnail_url'))
            if thumb_data:
                filename = f"video_{new_video.id}_{slugify(title[:30])}.jpg"
                new_video.thumbnail.save(filename, ContentFile(thumb_data), save=True)

            saved_count += 1

    total = Video.objects.filter(is_active=True).count()
    worship_total = Video.objects.filter(category=categories['proslavlenie'], is_active=True).count()
    print(f"Sync complete! New: {saved_count}, Updated: {updated_count}, Total active: {total} (Worship songs: {worship_total})")
    return {
        'new_count': saved_count,
        'updated_count': updated_count,
        'merged_count': merged_rt + merged_vk,
        'total': total,
        'worship_total': worship_total
    }


def trigger_background_auto_sync():
    """
    Фоновый автопилот с блокировкой на 3 часа:
    Запускается строго вне критического пути запроса.
    """
    lock_key = 'kclc_auto_sync_lock'
    if cache.get(lock_key):
        return False

    cache.set(lock_key, True, 10800)  # 3 часа

    def _worker():
        try:
            print("[AUTO-SYNC] Starting background sync for videos & podcasts...")
            from church_app.services_podcast_sync import sync_podcasts
            sync_videos()
            sync_podcasts()
            print("[AUTO-SYNC] Background sync finished successfully.")
        except Exception as e:
            print(f"[AUTO-SYNC] Error during background sync: {e}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return True
