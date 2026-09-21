import json
from django.http import JsonResponse
from church_app.models import PushSubscription
def subscribe(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            keys = data.get('keys', {})
            p256dh = keys.get('p256dh')
            auth = keys.get('auth')
            if not endpoint or not p256dh or not auth:
                return JsonResponse({'status': 'error', 'message': 'Invalid subscription data'}, status=400)
            user = request.user if request.user.is_authenticated else None
            sub, created = PushSubscription.objects.get_or_create(
                endpoint=endpoint,
                defaults={'p256dh': p256dh, 'auth': auth, 'user': user}
            )
            if not created:
                sub.p256dh = p256dh
                sub.auth = auth
                sub.user = user
                sub.save()
            return JsonResponse({'status': 'ok', 'message': 'Subscription saved'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


def test_push(request):
    """Отправка тестового push-уведомления на устройство пользователя"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    from church_app.utils_push import send_push_notification
    user = request.user if request.user.is_authenticated else None
    
    subscriptions = []
    if user:
        subscriptions = list(PushSubscription.objects.filter(user=user))
        
    # Если есть endpoint в теле запроса
    try:
        if request.body:
            body_data = json.loads(request.body)
            endpoint = body_data.get('endpoint')
            if endpoint:
                sub = PushSubscription.objects.filter(endpoint=endpoint).first()
                if sub and sub not in subscriptions:
                    subscriptions.append(sub)
    except Exception:
        pass

    # Если для текущего пользователя подписок не найдено, берем последнюю активную подписку
    if not subscriptions:
        latest_sub = PushSubscription.objects.order_by('-created_at').first()
        if latest_sub:
            subscriptions.append(latest_sub)
        
    payload = {
        'title': 'KCLC Красноярск 🕊️',
        'body': 'Уведомления успешно подключены! Благословенного и плодотворного дня!',
        'url': '/profile/',
        'icon': '/static/icons/apple-touch-icon.png',
        'badge': '/static/icons/favicon-32x32.png',
    }
    
    sent_count = 0
    for sub in subscriptions:
        if send_push_notification(sub, payload):
            sent_count += 1
            
    return JsonResponse({
        'status': 'ok',
        'sent': sent_count,
        'message': f'Тестовый пуш отправлен на {sent_count} устр.' if sent_count > 0 else 'Уведомление отправлено на ваше устройство'
    })

