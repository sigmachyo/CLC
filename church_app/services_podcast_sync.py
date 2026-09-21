import urllib.request
import xml.etree.ElementTree as ET
import re
from church_app.models import PodcastEpisode

PODCAST_RSS_URL = 'https://kclcfamily.podster.fm/rss.xml'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}


def parse_speaker(title: str) -> tuple:
    """Пытается извлечь спикера и чистое название из заголовка эпизода"""
    # Часто заголовок имеет вид: "ТЕМА - Спикер" или "ТЕМА / Спикер" или "ТЕМА | Спикер"
    for sep in [' - ', ' — ', ' – ', ' | ', ' / ']:
        if sep in title:
            parts = title.split(sep, 1)
            # Проверяем, похоже ли вторая часть на ФИО
            if len(parts[1].strip().split()) in [1, 2, 3]:
                return parts[0].strip(), parts[1].strip()
            if len(parts[0].strip().split()) in [1, 2, 3]:
                return parts[1].strip(), parts[0].strip()
    return title.strip(), "ЦХЖ Красноярск"


def sync_podcasts():
    """Синхронизирует эпизоды подкаста с официального RSS kclcfamily.podster.fm"""
    print(f"Fetching podcast RSS feed from {PODCAST_RSS_URL}...")
    req = urllib.request.Request(PODCAST_RSS_URL, headers=HEADERS)
    res = urllib.request.urlopen(req, timeout=12)
    xml_data = res.read()
    root = ET.fromstring(xml_data)

    channel = root.find('channel')
    if channel is None:
        print("Invalid RSS feed format: no channel element")
        return {'new': 0, 'updated': 0, 'total': PodcastEpisode.objects.count()}

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

        # Ищем существующий выпуск по episode_url, audio_url или названию
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

