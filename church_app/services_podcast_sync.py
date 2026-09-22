import requests
import xml.etree.ElementTree as ET
import re
from church_app.models import PodcastEpisode

PODCAST_RSS_URL = 'https://kclcfamily.podster.fm/rss.xml'
FALLBACK_RSS_URL = 'https://podster.fm/rss.xml?podcast=46787'
RSS2JSON_API_URL = 'https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fkclcfamily.podster.fm%2Frss.xml'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
}


def parse_speaker(title: str) -> tuple:
    """Пытается извлечь спикера и чистое название из заголовка эпизода"""
    for sep in [' - ', ' — ', ' – ', ' | ', ' / ']:
        if sep in title:
            parts = title.split(sep, 1)
            if len(parts[1].strip().split()) in [1, 2, 3]:
                return parts[0].strip(), parts[1].strip()
            if len(parts[0].strip().split()) in [1, 2, 3]:
                return parts[1].strip(), parts[0].strip()
    return title.strip(), "ЦХЖ Красноярск"


def sync_podcasts_via_rss2json():
    """Резервный метод синхронизации через rss2json (обходит Cloudflare 403 на хостингах)"""
    print(f"Fetching podcast feed via rss2json API proxy...")
    try:
        r = requests.get(RSS2JSON_API_URL, timeout=15)
        data = r.json()
        if data.get('status') != 'ok':
            print(f"rss2json returned status: {data.get('status')}")
            return {'new': 0, 'updated': 0, 'total': PodcastEpisode.objects.count()}

        items = data.get('items', [])
        created_count = 0
        updated_count = 0

        for idx, item in enumerate(items):
            raw_title = item.get('title', '').strip()
            if not raw_title:
                continue

            clean_title, speaker = parse_speaker(raw_title)
            episode_url = item.get('link', '').strip()
            enclosure = item.get('enclosure', {})
            audio_url = enclosure.get('link', '').strip() if isinstance(enclosure, dict) else ''

            dur_raw = enclosure.get('duration') if isinstance(enclosure, dict) else None
            duration = ''
            if dur_raw:
                try:
                    secs = int(dur_raw)
                    if secs >= 3600:
                        duration = f"{secs // 3600}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"
                    else:
                        duration = f"{secs // 60}:{secs % 60:02d}"
                except (ValueError, TypeError):
                    duration = str(dur_raw)

            episode = None
            if audio_url:
                episode = PodcastEpisode.objects.filter(audio_url=audio_url).first()
            if not episode and episode_url:
                episode = PodcastEpisode.objects.filter(episode_url=episode_url).first()
            if not episode:
                episode = PodcastEpisode.objects.filter(title=clean_title).first()

            if episode:
                changed = False
                if audio_url and episode.audio_url != audio_url:
                    episode.audio_url = audio_url
                    changed = True
                if episode_url and episode.episode_url != episode_url:
                    episode.episode_url = episode_url
                    changed = True
                if duration and not episode.duration:
                    episode.duration = duration
                    changed = True
                if speaker and not episode.speaker:
                    episode.speaker = speaker
                    changed = True
                if changed:
                    episode.save()
                    updated_count += 1
            else:
                PodcastEpisode.objects.create(
                    title=clean_title[:300],
                    speaker=speaker[:200],
                    duration=duration[:20],
                    episode_url=episode_url[:500],
                    audio_url=audio_url[:1000],
                    order=idx,
                    is_active=True
                )
                created_count += 1

        total = PodcastEpisode.objects.filter(is_active=True).count()
        print(f"[rss2json] Podcast sync finished! Created: {created_count}, Updated: {updated_count}, Total active: {total}")
        return {'new': created_count, 'updated': updated_count, 'total': total}
    except Exception as e:
        print(f"Error fetching podcasts via rss2json: {e}")
        return {'new': 0, 'updated': 0, 'total': PodcastEpisode.objects.count()}


def sync_podcasts():
    """Синхронизирует эпизоды подкаста с официального RSS kclcfamily.podster.fm"""
    print(f"Fetching podcast RSS feed from {PODCAST_RSS_URL}...")
    xml_data = None
    try:
        r = requests.get(PODCAST_RSS_URL, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            xml_data = r.content
        else:
            print(f"Main RSS returned {r.status_code}, trying fallback {FALLBACK_RSS_URL}...")
            r_fb = requests.get(FALLBACK_RSS_URL, headers=HEADERS, timeout=15)
            if r_fb.status_code == 200:
                xml_data = r_fb.content
    except Exception as e:
        print(f"Direct RSS fetch failed: {e}")

    # Если прямой доступ заблокирован Cloudflare (403), используем rss2json прокси
    if not xml_data:
        print("Direct Podster fetch unavailable, switching to rss2json proxy...")
        return sync_podcasts_via_rss2json()

    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        print(f"Error parsing XML from Podster: {e}, falling back to rss2json...")
        return sync_podcasts_via_rss2json()

    channel = root.find('channel')
    if channel is None:
        return sync_podcasts_via_rss2json()

    items = channel.findall('item')
    print(f"Found {len(items)} episodes in RSS feed.")

    itunes_ns = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}

    created_count = 0
    updated_count = 0

    for idx, item in enumerate(items):
        title_elem = item.find('title')
        raw_title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''
        if not raw_title:
            continue

        clean_title, speaker = parse_speaker(raw_title)

        link_elem = item.find('link')
        episode_url = link_elem.text.strip() if link_elem is not None and link_elem.text else ''

        enclosure = item.find('enclosure')
        audio_url = enclosure.attrib.get('url', '') if enclosure is not None else ''

        duration_elem = item.find('itunes:duration', itunes_ns)
        duration = duration_elem.text.strip() if duration_elem is not None and duration_elem.text else ''

        episode = None
        if audio_url:
            episode = PodcastEpisode.objects.filter(audio_url=audio_url).first()
        if not episode and episode_url:
            episode = PodcastEpisode.objects.filter(episode_url=episode_url).first()
        if not episode:
            episode = PodcastEpisode.objects.filter(title=clean_title).first()

        if episode:
            changed = False
            if audio_url and episode.audio_url != audio_url:
                episode.audio_url = audio_url
                changed = True
            if episode_url and episode.episode_url != episode_url:
                episode.episode_url = episode_url
                changed = True
            if duration and not episode.duration:
                episode.duration = duration
                changed = True
            if speaker and not episode.speaker:
                episode.speaker = speaker
                changed = True
            if changed:
                episode.save()
                updated_count += 1
        else:
            PodcastEpisode.objects.create(
                title=clean_title[:300],
                speaker=speaker[:200],
                duration=duration[:20],
                episode_url=episode_url[:500],
                audio_url=audio_url[:1000],
                order=idx,
                is_active=True
            )
            created_count += 1

    total = PodcastEpisode.objects.filter(is_active=True).count()
    print(f"Podcast sync finished! Created: {created_count}, Updated: {updated_count}, Total active: {total}")
    return {'new': created_count, 'updated': updated_count, 'total': total}
