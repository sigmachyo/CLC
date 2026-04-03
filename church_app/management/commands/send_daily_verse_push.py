import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from pywebpush import webpush, WebPushException
from church_app.models import PushSubscription, DailyVerse

class Command(BaseCommand):
    help = 'Отправить Стих Дня всем подписанным пользователям'

    def handle(self, *args, **options):
        today = timezone.localdate()
        daily_verse = DailyVerse.objects.filter(date=today).first() or DailyVerse.objects.order_by('-date').first()
        
        if not daily_verse:
            self.stdout.write(self.style.WARNING("Нет доступного стиха дня."))
            return
            
        payload = {
            'title': 'Стих дня',
            'body': f'{daily_verse.verse_text} - {daily_verse.reference}',
            'url': '/library/'
        }
        
        subscriptions = PushSubscription.objects.all()
        count = 0
        deleted = 0
        
        for sub in subscriptions:
            try:
                sub_info = {
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                }
                
                webpush(
                    subscription_info=sub_info,
                    data=json.dumps(payload),
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": settings.VAPID_ADMIN_EMAIL}
                )
                count += 1
            except WebPushException as ex:
                self.stderr.write(self.style.ERROR(f"Провал отправки к {sub.endpoint}: {repr(ex)}"))
                if ex.response and ex.response.status_code in [404, 410]:
                    sub.delete()
                    deleted += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Неизвестная ошибка: {e}"))
                
        self.stdout.write(self.style.SUCCESS(f"Успешно отправлено {count} уведомлений. Удалено устаревших подписок: {deleted}"))
