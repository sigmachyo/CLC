import requests
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from church_app.models import News, Event
import datetime

class Command(BaseCommand):
    help = 'Импорт новостей и событий из WordPress (kclc.ru)'

    def handle(self, *args, **options):
        self.stdout.write("Начинаем синхронизацию данных с kclc.ru...")
        
        # 1. Синхронизация Новостей
        self.sync_news()
        
        # 2. Синхронизация Событий (конференций)
        # self.sync_events()
        
        self.stdout.write(self.style.SUCCESS("Синхронизация успешно завершена!"))

    def sync_news(self):
        url = "https://kclc.ru/wp-json/wp/v2/posts?per_page=20"
        response = requests.get(url)
        if response.status_code == 200:
            posts = response.json()
            count = 0
            for post in posts:
                # Поиск существующей новости по slug, чтобы не дублировать
                news, created = News.objects.get_or_create(
                    slug=post['slug'],
                    defaults={
                        'title': post['title']['rendered'],
                        'content': post['content']['rendered'],
                        'published_date': parse_datetime(post['date']),
                    }
                )
                if created:
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"Импортировано {count} новых новостей."))
        else:
            self.stdout.write(self.style.ERROR("Ошибка при загрузке постов WP."))

