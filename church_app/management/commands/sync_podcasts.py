from django.core.management.base import BaseCommand
from church_app.services_podcast_sync import sync_podcasts

class Command(BaseCommand):
    help = 'Синхронизирует выпуски подкаста с официального RSS-канала kclcfamily.podster.fm'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Начинаем синхронизацию подкастов с podster.fm..."))
        stats = sync_podcasts()
        self.stdout.write(self.style.SUCCESS(
            f"Синхронизация подкастов успешно завершена!\n"
            f"- Создано новых: {stats['new']}\n"
            f"- Обновлено: {stats['updated']}\n"
            f"- Всего выпусков в базе: {stats['total']}"
        ))
