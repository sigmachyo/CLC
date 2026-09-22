from django.core.management.base import BaseCommand
from church_app.services_video_sync import sync_videos
from church_app.services_podcast_sync import sync_podcasts
from django.core.cache import cache
from django.utils import timezone


class Command(BaseCommand):
    help = 'Полная автоматическая синхронизация всего контента: YouTube (@kclcfamily, @kclcworship), RuTube, VK и подкастов Podster'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== НАЧАЛО АВТОМАТИЧЕСКОЙ СИНХРОНИЗАЦИИ КОНТЕНТА KCLC ==="))

        # 1. Синхронизация видео и прославления
        try:
            self.stdout.write("1. Синхронизация YouTube и RuTube видео (включая @kclcworship)...")
            video_stats = sync_videos()
            self.stdout.write(self.style.SUCCESS(
                f"   [Видео] Создано новых: {video_stats.get('new_count', 0)}, "
                f"Обновлено: {video_stats.get('updated_count', 0)}, "
                f"Всего в базе: {video_stats.get('total', 0)}"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [Ошибка видео]: {e}"))

        # 2. Синхронизация подкастов
        try:
            self.stdout.write("2. Синхронизация подкастов Podster.fm...")
            podcast_stats = sync_podcasts()
            self.stdout.write(self.style.SUCCESS(
                f"   [Подкасты] Создано новых: {podcast_stats.get('new', 0)}, "
                f"Обновлено: {podcast_stats.get('updated', 0)}, "
                f"Всего в базе: {podcast_stats.get('total', 0)}"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [Ошибка подкастов]: {e}"))

        # 3. Фиксация времени успешной синхронизации в кеше
        cache.set('kclc_last_content_sync', timezone.now().isoformat(), timeout=86400 * 7)
        self.stdout.write(self.style.SUCCESS("=== ВСЯ СИНХРОНИЗАЦИЯ УСПЕШНО ЗАВЕРШЕНА ==="))

