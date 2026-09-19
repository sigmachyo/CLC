import os
from django.conf import settings


def oauth_providers_status(request):
    """
    Проверяет, настроены ли реальные ключи авторизации для VK и Яндекс.
    Если ключи не настроены, интерфейс показывает дружелюбную подсказку вместо ошибки 400.
    """
    vk_id = os.environ.get('VK_CLIENT_ID', '').strip()
    yandex_id = os.environ.get('YANDEX_CLIENT_ID', '').strip()

    return {
        'oauth_vk_ready': bool(vk_id and vk_id != 'change-me'),
        'oauth_yandex_ready': bool(yandex_id and yandex_id != 'change-me'),
    }
