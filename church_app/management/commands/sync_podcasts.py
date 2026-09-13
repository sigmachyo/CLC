import re
import xml.etree.ElementTree as ElementTree

import requests
from django.core.management.base import BaseCommand, CommandError

from church_app.models import PodcastEpisode


RSS_URL = 'https://podster.fm/rss.xml?pid=46787'
ITUNES_NS = 'http://www.itunes.com/dtds/podcast-1.0.dtd'


class Command(BaseCommand):
    help = 'Импортирует полный архив подкаста из публичного RSS Podster'

    def handle(self, *args, **options):
        try:
            response = requests.get(
                RSS_URL,
                headers={'User-Agent': 'KCLC local sync/1.0'},
                timeout=30,
            )
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
        except (requests.RequestException, ElementTree.ParseError) as error:
            raise CommandError(f'Не удалось загрузить RSS подкаста: {error}')

        episodes = []
        for order, item in enumerate(root.findall('./channel/item')):
            title = (item.findtext('title') or '').strip()
            episode_url = (item.findtext('link') or '').strip()
            enclosure = item.find('enclosure')
            audio_url = enclosure.get('url', '').strip() if enclosure is not None else ''
            duration = (item.findtext(f'{{{ITUNES_NS}}}duration') or '').strip()
            speaker = ''
            if ' - ' in title:
                title, speaker = title.rsplit(' - ', 1)
            title = re.sub(r'\s+', ' ', title).strip()
            episodes.append(PodcastEpisode(
                title=title[:300],
                speaker=speaker[:200],
                duration=duration[:20],
                episode_url=episode_url[:500],
                audio_url=audio_url[:1000],
                order=order,
                is_active=True,
            ))

        PodcastEpisode.objects.all().delete()
        PodcastEpisode.objects.bulk_create(episodes)
        self.stdout.write(self.style.SUCCESS(f'Импортировано выпусков подкаста: {len(episodes)}'))
