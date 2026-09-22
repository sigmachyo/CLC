import json
import os
from django.core.management.base import BaseCommand
from church_app.models import PodcastEpisode, Event, News, HomeGroup, PastorPhoto, DailyVerse


class Command(BaseCommand):
    help = 'Безопасный импорт данных без конфликтов первичных ключей и уникальных полей'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='?', default='clean_content.json', help='Путь к JSON файлу с данными')

    def handle(self, *args, **options):
        filepath = options['file']
        if not os.path.isabs(filepath):
            filepath = os.path.join(os.getcwd(), filepath)

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f"Файл {filepath} не найден!"))
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(self.style.NOTICE(f"Загрузка {len(data)} объектов из {filepath}..."))

        stats = {
            'podcasts': {'created': 0, 'updated': 0},
            'events': {'created': 0, 'updated': 0},
            'news': {'created': 0, 'updated': 0},
            'homegroups': {'created': 0, 'updated': 0},
            'pastors': {'created': 0, 'updated': 0},
            'verses': {'created': 0, 'updated': 0},
        }

        for item in data:
            model = item['model']
            fields = item['fields']

            if model == 'church_app.podcastepisode':
                audio_url = fields.get('audio_url', '')
                episode_url = fields.get('episode_url', '')
                title = fields.get('title', '')

                ep = None
                if audio_url:
                    ep = PodcastEpisode.objects.filter(audio_url=audio_url).first()
                if not ep and episode_url:
                    ep = PodcastEpisode.objects.filter(episode_url=episode_url).first()
                if not ep and title:
                    ep = PodcastEpisode.objects.filter(title=title).first()

                if ep:
                    for k, v in fields.items():
                        setattr(ep, k, v)
                    ep.save()
                    stats['podcasts']['updated'] += 1
                else:
                    PodcastEpisode.objects.create(**fields)
                    stats['podcasts']['created'] += 1

            elif model == 'church_app.event':
                slug = fields.get('slug')
                ev = Event.objects.filter(slug=slug).first()
                if ev:
                    for k, v in fields.items():
                        setattr(ev, k, v)
                    ev.save()
                    stats['events']['updated'] += 1
                else:
                    Event.objects.create(**fields)
                    stats['events']['created'] += 1

            elif model == 'church_app.news':
                slug = fields.get('slug')
                nw = News.objects.filter(slug=slug).first()
                if nw:
                    for k, v in fields.items():
                        setattr(nw, k, v)
                    nw.save()
                    stats['news']['updated'] += 1
                else:
                    News.objects.create(**fields)
                    stats['news']['created'] += 1

            elif model == 'church_app.homegroup':
                hg = None
                pk = item.get('pk')
                if pk:
                    hg = HomeGroup.objects.filter(id=pk).first()
                if not hg:
                    hg = HomeGroup.objects.filter(
                        district=fields.get('district'),
                        address=fields.get('address'),
                        leader_name=fields.get('leader_name')
                    ).first()

                if hg:
                    for k, v in fields.items():
                        setattr(hg, k, v)
                    hg.save()
                    stats['homegroups']['updated'] += 1
                else:
                    HomeGroup.objects.create(**fields)
                    stats['homegroups']['created'] += 1

            elif model == 'church_app.pastorphoto':
                slug = fields.get('slug')
                pp = PastorPhoto.objects.filter(slug=slug).first()
                if pp:
                    for k, v in fields.items():
                        setattr(pp, k, v)
                    pp.save()
                    stats['pastors']['updated'] += 1
                else:
                    PastorPhoto.objects.create(**fields)
                    stats['pastors']['created'] += 1

            elif model == 'church_app.dailyverse':
                dv = DailyVerse.objects.filter(id=item.get('pk')).first()
                if not dv:
                    dv = DailyVerse.objects.filter(verse_text=fields.get('verse_text')).first()
                if dv:
                    for k, v in fields.items():
                        setattr(dv, k, v)
                    dv.save()
                    stats['verses']['updated'] += 1
                else:
                    DailyVerse.objects.create(**fields)
                    stats['verses']['created'] += 1

        self.stdout.write(self.style.SUCCESS(f"Подкасты: {stats['podcasts']} (Всего: {PodcastEpisode.objects.count()})"))
        self.stdout.write(self.style.SUCCESS(f"Мероприятия: {stats['events']} (Всего: {Event.objects.count()})"))
        self.stdout.write(self.style.SUCCESS(f"Новости: {stats['news']} (Всего: {News.objects.count()})"))
        self.stdout.write(self.style.SUCCESS(f"Домашние группы: {stats['homegroups']} (Всего: {HomeGroup.objects.count()})"))
        self.stdout.write(self.style.SUCCESS(f"Пасторы: {stats['pastors']} (Всего: {PastorPhoto.objects.count()})"))
        self.stdout.write(self.style.SUCCESS(f"Стихи дня: {stats['verses']} (Всего: {DailyVerse.objects.count()})"))

