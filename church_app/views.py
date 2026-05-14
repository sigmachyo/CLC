from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from pathlib import Path
from .models import Announcement, DailyVerse, HeroBackground, Event, Video, Category, PrayerRequest, UserBibleProgress, EventRegistration
from .forms import RegisterForm, LoginForm, ProfileEditForm, ChangePasswordForm
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET, require_POST
import datetime
import requests
import re
import json as _json
import logging
import pytz
from datetime import datetime as dt, timedelta
from zoneinfo import ZoneInfo
from django.http import HttpResponse
from django.conf import settings
import os

logger = logging.getLogger(__name__)
RUTUBE_CHANNEL_ID = '39733690'
RUTUBE_API_URL = f'https://rutube.ru/api/video/person/{RUTUBE_CHANNEL_ID}/?page=1&format=json'
YT_CHANNEL_HANDLE = 'kclcfamily'
YT_STREAMS_URL = f'https://www.youtube.com/@{YT_CHANNEL_HANDLE}/streams'
STREAM_KEYWORDS = ['ВОСКРЕСНОЕ СЛУЖЕНИЕ', 'ВОСКРЕСНОЕ', 'СЛУЖЕНИЕ']
SCHEDULE = {
    'weekday': 6,
    'hour': 11,
    'minute': 0,
    'timezone_offset': 7
}
_YT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'ru-RU,ru;q=0.9',
}
_YT_COOKIES = {
    'SOCS': 'CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjMwODI5LjA3X3AxGgJlbiACGgYIgJnSmgY',
}

KRA_TZ = ZoneInfo('Asia/Krasnoyarsk')

def _kra_now():
    """Текущее время в Красноярске"""
    return timezone.now().astimezone(KRA_TZ)

def _service_time_today_kra():
    """Время начала служения сегодня (в Красноярске), как aware datetime"""
    kra = _kra_now()
    return kra.replace(hour=SCHEDULE['hour'], minute=SCHEDULE['minute'], second=0, microsecond=0)

def get_current_service_start():
    """
    Если сейчас воскресенье и мы в окне трансляции (от начала до +3ч),
    возвращает время начала текущего служения (UTC).
    Иначе возвращает None.
    """
    kra = _kra_now()
    if kra.weekday() != SCHEDULE['weekday']:
        return None
    service_start_kra = _service_time_today_kra()
    service_end_kra = service_start_kra + timedelta(hours=3)
    # Трансляция идёт в диапазоне [11:00, 14:00), то есть 14:00 это уже конец
    if service_start_kra <= kra < service_end_kra:
        return service_start_kra.astimezone(ZoneInfo('UTC'))
    return None

def get_next_sunday_service():
    """
    Вычисляет время СЛЕДУЮЩЕГО (будущего) воскресного служения.
    Если сейчас идёт трансляция, возвращает СЛЕДУЮЩЕЕ воскресенье.
    Если трансляция ещё не началась сегодня, возвращает сегодня.
    """
    kra = _kra_now()
    service_today = _service_time_today_kra()
    days_ahead = SCHEDULE['weekday'] - kra.weekday()
    if days_ahead < 0:
        days_ahead += 7
    if days_ahead == 0:
        # Если сегодня воскресенье, проверяем, прошло ли время служения
        if kra >= service_today:
            # Служение уже прошло, берём следующее воскресенье
            days_ahead = 7
        # Иначе служение ещё впереди сегодня, days_ahead остаётся 0
    next_service_kra = service_today + timedelta(days=days_ahead)
    return next_service_kra.astimezone(ZoneInfo('UTC'))

def is_stream_live():
    """Проверяет, идёт ли сейчас прямая трансляция (окно 3 часа от начала)"""
    return get_current_service_start() is not None

def get_time_until_service():
    """
    Возвращает время до начала следующей службы.
    Таймер показывается ТОЛЬКО для предстоящей трансляции.
    Если трансляция идёт — is_live=True, таймер обнулён.
    """
    now = timezone.now()
    live = is_stream_live()
    if live:
        return {
            'days': 0,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
            'is_live': True,
            'until_next_week': False
        }
    
    # Получаем время следующего служения в UTC
    next_service = get_next_sunday_service()
    
    # Убеждаемся, что обе даты в UTC для корректного сравнения
    if now.tzinfo is None:
        now = pytz.utc.localize(now)
    
    delta = next_service - now
    
    # Если время уже прошло, значит ошибка в расчётах
    if delta.total_seconds() < 0:
        # Пересчитываем следующее воскресенье
        kra = _kra_now()
        service_kra = _service_time_today_kra()
        # Принудительно ищем СЛЕДУЮЩЕЕ воскресенье
        next_service = (service_kra + timedelta(days=7)).astimezone(ZoneInfo('UTC'))
        delta = next_service - now
    
    total_seconds = max(0, delta.total_seconds())
    days = int(total_seconds // 86400)
    hours = int((total_seconds % 86400) // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'is_live': False,
        'until_next_week': False
    }

@require_GET
@cache_page(5)  # Короткий кеш для быстрого переключения состояний LIVE/TIMER
def rutube_stream_api(request):
    """
    Запрашивает API Rutube канала.
    Возвращает JSON с video_id последнего воскресного служения.
    """
    try:
        resp = requests.get(RUTUBE_API_URL, timeout=20, headers={
            'User-Agent': _YT_HEADERS['User-Agent'],
        })
        resp.raise_for_status()
    except requests.Timeout:
        return JsonResponse(
            {'video_id': None, 'error': 'Rutube timeout', 'platform': 'rutube'},
            status=503
        )
    except requests.RequestException as e:
        return JsonResponse(
            {'video_id': None, 'error': f'network: {e}', 'platform': 'rutube'},
            status=503
        )
    try:
        data = resp.json()
    except Exception as e:
        logger.error(f'Ошибка парсинга ответа Rutube API: {e}. Тело ответа: {resp.text[:500]}')
        return JsonResponse(
            {'video_id': None, 'error': f'parse error: {e}', 'platform': 'rutube'},
            status=500
        )
    results = data.get('results', [])
    if not results:
        return JsonResponse(
            {'video_id': None, 'error': 'Видео не найдены', 'platform': 'rutube'},
            status=404
        )
    all_valid_entries = []
    stream_entries = []
    
    for item in results:
        # Проверка на модерацию и доступность
        if item.get('is_moderation', False): continue
        if not item.get('is_active', True): continue
        
        title = item.get('title', '').strip()
        video_id = None
        embed_url = item.get('embed_url', '')
        if embed_url:
            video_id = embed_url.rstrip('/').split('/')[-1]
        
        if not video_id: continue
        
        is_stream = any(kw.upper() in title.upper() for kw in STREAM_KEYWORDS)
        published = item.get('created_at', '')
        
        entry = {
            'video_id': str(video_id),
            'title': title,
            'is_stream': is_stream,
            'published': published,
            'thumbnail': item.get('thumbnail_url', ''),
        }
        all_valid_entries.append(entry)
        if is_stream:
            stream_entries.append(entry)

    if not all_valid_entries:
        return JsonResponse(
            {'video_id': None, 'error': 'Доступные видео не найдены', 'platform': 'rutube'},
            status=404
        )

    best = stream_entries[0] if stream_entries else all_valid_entries[0]
    
    # [LOGIC] Синхронизация с библиотекой (авто-добавление)
    try:
        video_full_url = f"https://rutube.ru/video/{best['video_id']}/"
        if not Video.objects.filter(rutube_url=video_full_url).exists():
            # Находим категорию Видео
            cat = Category.objects.filter(category_type='video').first()
            if cat:
                desc = f"Автоматически добавлено из трансляции. Дата: {best['published']}"
                if best.get('thumbnail'):
                    desc += f"\nПревью: {best['thumbnail']}"
                Video.objects.create(
                    title=best['title'],
                    description=desc,
                    category=cat,
                    rutube_url=video_full_url,
                    is_active=True
                )
    except Exception as e:
        logger.warning(f"Ошибка авто-записи трансляции в БД: {e}")

    is_live = is_stream_live()
    return JsonResponse({
        'video_id': best['video_id'],
        'title': best['title'],
        'is_stream': best['is_stream'],
        'is_live': is_live,
        'platform': 'rutube',
        'channel_id': RUTUBE_CHANNEL_ID,
        'all_streams': stream_entries[:5],
        'latest_video': all_valid_entries[0],
    })

def _parse_streams_page(html):
    """Парсит HTML страницы /streams канала YouTube"""
    match = re.search(r'var\s+ytInitialData\s*=\s*({.+?})\s*;\s*', html)
    if not match:
        return []
    try:
        data = _json.loads(match.group(1))
    except _json.JSONDecodeError:
        return []
    results = []
    seen_ids = set()
    def _extract_videos(obj):
        if isinstance(obj, dict):
            if 'videoRenderer' in obj:
                vr = obj['videoRenderer']
                vid = vr.get('videoId', '')
                if not vid or vid in seen_ids:
                    return
                seen_ids.add(vid)
                title_obj = vr.get('title', {})
                if 'runs' in title_obj:
                    title = ''.join(r.get('text', '') for r in title_obj['runs'])
                else:
                    title = title_obj.get('simpleText', '')
                title = title.strip()
                is_stream = any(kw.upper() in title.upper() for kw in STREAM_KEYWORDS)
                results.append({
                    'video_id': vid,
                    'title': title,
                    'published': '',
                    'is_stream': is_stream,
                })
                return
            for v in obj.values():
                _extract_videos(v)
        elif isinstance(obj, list):
            for item in obj:
                _extract_videos(item)
    _extract_videos(data)
    return results

@require_GET
@cache_page(5)  # Короткий кеш для быстрого переключения состояний LIVE/TIMER
def live_stream_api(request):
    """Резервный API для YouTube"""
    try:
        resp = requests.get(YT_STREAMS_URL, timeout=10, headers=_YT_HEADERS, cookies=_YT_COOKIES)
        resp.raise_for_status()
    except requests.Timeout:
        return JsonResponse(
            {'video_id': None, 'error': 'YouTube timeout', 'platform': 'youtube'},
            status=503
        )
    except requests.RequestException as e:
        return JsonResponse(
            {'video_id': None, 'error': f'network: {e}', 'platform': 'youtube'},
            status=503
        )
    try:
        entries = _parse_streams_page(resp.text)
    except Exception as e:
        logger.exception('Ошибка парсинга страницы YouTube streams')
        return JsonResponse(
            {'video_id': None, 'error': f'parse error: {e}', 'platform': 'youtube'},
            status=500
        )
    if not entries:
        return JsonResponse(
            {'video_id': None, 'error': 'Видео не найдены', 'platform': 'youtube'},
            status=404
        )
    stream_entries = [e for e in entries if e['is_stream']]
    best = stream_entries[0] if stream_entries else entries[0]
    is_live = is_stream_live()
    return JsonResponse({
        'video_id': best['video_id'],
        'title': best['title'],
        'published': best['published'],
        'is_stream': best['is_stream'],
        'is_live': is_live,
        'platform': 'youtube',
        'channel_handle': YT_CHANNEL_HANDLE,
        'all_streams': stream_entries[:5],
    })

@require_GET
@cache_page(5)  # Короткий кеш для быстрого переключения состояний LIVE/TIMER
def video_api(request):
    """
    Единый API для получения видео.
    Сначала пробует Rutube, при ошибке - YouTube.
    """
    rutube_resp = rutube_stream_api(request)
    if rutube_resp.status_code == 200:
        data = _json.loads(rutube_resp.content)
        if data.get('video_id'):
            data['time_until_service'] = get_time_until_service()
            return JsonResponse(data)
    yt_resp = live_stream_api(request)
    if yt_resp.status_code == 200:
        data = _json.loads(yt_resp.content)
        if data.get('video_id'):
            data['time_until_service'] = get_time_until_service()
            return JsonResponse(data)
    return JsonResponse({
        'video_id': None,
        'error': 'Видео недоступно',
        'platform': None,
        'time_until_service': get_time_until_service()
    }, status=404)

@require_GET
def debug_stream_status(request):
    """Debug API - показывает текущее состояние трансляции"""
    kra = _kra_now()
    service_today = _service_time_today_kra()
    next_service = get_next_sunday_service()
    
    return JsonResponse({
        'server_time_kra': kra.isoformat(),
        'server_time_utc': timezone.now().isoformat(),
        'day_of_week': kra.weekday(),  # 0=Monday, 6=Sunday
        'hour': kra.hour,
        'minute': kra.minute,
        'is_sunday': kra.weekday() == SCHEDULE['weekday'],
        'service_start_today_kra': service_today.isoformat(),
        'is_stream_live': is_stream_live(),
        'time_until_service': get_time_until_service(),
        'next_service_utc': next_service.isoformat(),
        'schedule': SCHEDULE,
    })

from .models import News

def home(request):
    """Главная страница с таймером воскресной трансляции"""
    current_announcement = Announcement.objects.filter(
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).first()
    time_info = get_time_until_service()
    featured_events = Event.objects.filter(is_active=True, is_featured=True).order_by('start_date')[:10]
    
    # Получаем текущее UTC время в миллисекундах
    # Это критично - должны быть миллисекунды от эпохи в UTC
    server_now_ms = int(timezone.now().timestamp() * 1000)

    news = News.objects.filter(
        is_active=True
    )[:6]
    
    context = {
        'announcement': current_announcement,
        'show_announcement': current_announcement is not None,
        'user': request.user,
        'time_until_service': time_info,
        'is_live': time_info['is_live'],
        'service_schedule': SCHEDULE,
        'featured_events': featured_events,
        'server_now_ms': server_now_ms,
        'server_now_kra': _kra_now().isoformat(),
        'news': news,
    }
    return render(request, 'home.html', context)

def offline_view(request):
    """Страница при отсутствии интернета"""
    return render(request, 'offline.html')

def register_view(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
            )
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация прошла успешно!')
            return redirect('home')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            for field in form:
                for error in field.errors:
                    messages.error(request, f'{field.label}: {error}')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    """Вход пользователя"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                messages.success(request, f'С возвращением, {user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

@require_POST
def logout_view(request):
    """Выход пользователя — только POST для защиты от CSRF"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('home')

@login_required
def profile_view(request):
    """Страница профиля"""
    user = request.user
    
    # Молитвы
    prayers = PrayerRequest.objects.filter(user=user).order_by('-created_at')
    prayers_count = prayers.count()
    recent_prayers = prayers[:3]
    
    # Изучено (планы)
    plans_count = UserBibleProgress.objects.filter(user=user, completed_at__isnull=False).count()
    
    # События
    events_count = EventRegistration.objects.filter(user=user).count()
    
    # Текущее обучение
    current_progress = UserBibleProgress.objects.filter(user=user, completed_at__isnull=True).order_by('-last_read_at').first()
    
    context = {
        'user': user,
        'prayers_count': prayers_count,
        'recent_prayers': recent_prayers,
        'plans_count': plans_count,
        'events_count': events_count,
        'current_progress': current_progress,
    }
    return render(request, 'profile.html', context)

@login_required
def profile_edit_view(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = ProfileEditForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
    return render(request, 'profile_edit.html', {'user': request.user, 'form': form})

@login_required
def change_password_view(request):
    """Смена пароля"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            if not user.check_password(form.cleaned_data['old_password']):
                messages.error(request, 'Текущий пароль неверен')
                return redirect('change_password')
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            login(request, user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('profile')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = ChangePasswordForm()
    return render(request, 'change_password.html', {'form': form})

@require_POST
def dismiss_announcement(request):
    """Закрытие объявления — только POST"""
    announcement_id = request.POST.get('announcement_id')
    if not announcement_id:
        return JsonResponse({'success': False, 'error': 'No ID provided'}, status=400)
    dismissed = request.session.get('dismissed_announcements', [])
    if announcement_id not in dismissed:
        dismissed.append(announcement_id)
        request.session['dismissed_announcements'] = dismissed
    return JsonResponse({'success': True})

@require_GET
def service_worker(request):
    """Служит sw.js из корня для корректной области видимости (scope)"""
    # Пробуем найти sw.js в STATICFILES_DIRS или BASE_DIR/static
    sw_path = settings.BASE_DIR / 'static' / 'sw.js'
    
    if not sw_path.exists():
        # Резервный поиск в STATIC_ROOT, если мы в production
        sw_path = Path(settings.STATIC_ROOT) / 'sw.js'

    if not sw_path.exists():
        logger.error(f"Service worker not found at {sw_path}")
        return HttpResponse("Service Worker not found", status=404)

    try:
        with open(sw_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='application/javascript')
    except IOError as e:
        logger.error(f"Error reading service worker: {e}")
        return HttpResponse(status=404)


@require_GET
def chrome_devtools_json(request):
    """Силим 404 для Chrome DevTools расширения"""
    return JsonResponse({}, status=200)


def custom_404(request, exception=None):
    """Кастомная страница 404"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Кастомная страница 500"""
    return render(request, '500.html', status=500)

from .models import News
from django.shortcuts import render, get_object_or_404


def news_detail(request, slug):
    """Детальная страница новости"""
    news_item = get_object_or_404(News, slug=slug, is_active=True)
    news_item.views_count += 1
    news_item.save(update_fields=['views_count'])
    
    # Похожие новости
    related_news = News.objects.filter(is_active=True).exclude(id=news_item.id).order_by('-created_at')[:3]
    
    context = {
        'news': news_item,
        'related_news': related_news,
    }
    return render(request, 'info/news_detail.html', context)  # ← изменили путь
def news_list(request):
    """Страница со списком всех новостей"""
    news_items = News.objects.filter(is_active=True).order_by('-is_featured', '-created_at')
    
    from django.core.paginator import Paginator
    paginator = Paginator(news_items, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    recent_news = news_items[:5]
    
    context = {
        'page_obj': page_obj,
        'recent_news': recent_news,
        'total_count': news_items.count(),
    }
    return render(request, 'info/news_list.html', context)