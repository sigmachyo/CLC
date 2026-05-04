import json
from django.conf import settings
from pywebpush import webpush, WebPushException

def send_push_notification(subscription, payload):
    """
    Отправляет Push уведомление конкретному пользователю
    subscription: Экземпляр модели PushSubscription
    payload: dict с данными (title, body, url)
    """
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth
                }
            },
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": settings.VAPID_ADMIN_EMAIL,
            }
        )
        return True
    except WebPushException as ex:
        # Если подписка недействительна (например, пользователь удалил из браузера)
        if ex.response and ex.response.status_code in [404, 410]:
            subscription.delete()
        print("WebPushException:", repr(ex))
        return False
    except Exception as e:
        print("Push Exception:", str(e))
        return False

def broadcast_push_notification(payload):
    """
    Отправляет уведомление всем подписанным пользователям.
    Возвращает (success_count, failed_count)
    """
    from church_app.models import PushSubscription
    success = 0
    failed = 0
    for sub in PushSubscription.objects.all():
        if send_push_notification(sub, payload):
            success += 1
        else:
            failed += 1
    return success, failed
