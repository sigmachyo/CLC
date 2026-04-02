import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from church_app.models import PushSubscription

@csrf_exempt
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

            # Create or update subscription
            sub, created = PushSubscription.objects.get_or_create(
                endpoint=endpoint,
                defaults={'p256dh': p256dh, 'auth': auth, 'user': user}
            )

            if not created:
                # Update keys and user if they changed
                sub.p256dh = p256dh
                sub.auth = auth
                sub.user = user
                sub.save()

            return JsonResponse({'status': 'ok', 'message': 'Subscription saved'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

# В будущем здесь добавим test_notification для проверки отправки через pywebpush
