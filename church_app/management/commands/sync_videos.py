from django.core.management.base import BaseCommand
from church_app.services_video_sync import sync_videos

class Command(BaseCommand):
    help = 'Синхронизирует видео с официальных каналов RuTube и YouTube (с дедупликацией)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Начинаем синхронизацию видео с RuTube и YouTube..."))
        stats = sync_videos()
        self.stdout.write(self.style.SUCCESS(
            f"Синхронизация успешно завершена!\n"
            f"- Создано новых: {stats['new_count']}\n"
            f"- Обновлено: {stats['updated_count']}\n"
            f"- Найдено и объединено дубликатов: {stats['merged_count']}\n"
            f"- Всего активных видео в базе: {stats['total']}"
        ))

