from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from pathlib import Path
from .models import (
    Announcement, DailyVerse, HeroBackground, Event, Video, PodcastEpisode, Category, 
    PrayerRequest, UserBibleProgress, EventRegistration, UserProfile, FavoriteVerse, 
    PrayerConnection, Revelation, RevelationReaction, Ministry, MinistryApplication, HomeGroup
)
from .forms import RegisterForm, LoginForm, ProfileEditForm, ChangePasswordForm, FavoriteVerseForm
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from django.views.decorators.cache import cache_page
from django.core.cache import cache
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
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
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
def rutube_stream_api(request):
    """
    Запрашивает API Rutube канала.
    Возвращает JSON с video_id последнего воскресного служения.
    Использует внутренний кэш на 5 минут для максимальной скорости отклика без зависаний.
    """
    cached_data = cache.get('rutube_stream_cache')
    if cached_data is not None:
        return JsonResponse(cached_data)

    try:
        resp = requests.get(RUTUBE_API_URL, timeout=2.5, headers={
            'User-Agent': _YT_HEADERS['User-Agent'],
        })
        resp.raise_for_status()
    except requests.Timeout:
        fallback = {'video_id': None, 'error': 'Rutube timeout', 'platform': 'rutube'}
        cache.set('rutube_stream_cache', fallback, 30)
        return JsonResponse(fallback, status=503)
    except requests.RequestException as e:
        fallback = {'video_id': None, 'error': f'network: {e}', 'platform': 'rutube'}
        cache.set('rutube_stream_cache', fallback, 30)
        return JsonResponse(fallback, status=503)
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
    payload = {
        'video_id': best['video_id'],
        'title': best['title'],
        'is_stream': best['is_stream'],
        'is_live': is_live,
        'platform': 'rutube',
        'channel_id': RUTUBE_CHANNEL_ID,
        'all_streams': stream_entries[:5],
        'latest_video': all_valid_entries[0],
    }
    cache.set('rutube_stream_cache', payload, 300)
    return JsonResponse(payload)

def _parse_streams_page(html):
    """Парсит HTML страницы /streams канала YouTube (поддержка modern lockupViewModel и videoRenderer)"""
    match = re.search(r'var\s+ytInitialData\s*=\s*({.+?})\s*;\s*', html)
    if not match:
        match = re.search(r'window\[\"ytInitialData\"\]\s*=\s*({.+?})\s*;\s*', html)
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
            if 'lockupViewModel' in obj:
                lvm = obj['lockupViewModel']
                vid = lvm.get('contentId', '')
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    meta = lvm.get('metadata', {}).get('lockupMetadataViewModel', {})
                    title = meta.get('title', {}).get('content', '').strip()
                    is_stream = any(kw.upper() in title.upper() for kw in STREAM_KEYWORDS)
                    results.append({
                        'video_id': vid,
                        'title': title,
                        'published': '',
                        'is_stream': is_stream,
                    })
                    return
            elif 'videoRenderer' in obj:
                vr = obj['videoRenderer']
                vid = vr.get('videoId', '')
                if vid and vid not in seen_ids:
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
def live_stream_api(request):
    """API для YouTube с кэшированием на 5 минут и автоматическим резервом из базы"""
    cached_data = cache.get('yt_stream_cache')
    if cached_data is not None:
        return JsonResponse(cached_data)

    entries = []
    try:
        resp = requests.get(YT_STREAMS_URL, timeout=3.0, headers=_YT_HEADERS, cookies=_YT_COOKIES)
        if resp.status_code == 200:
            entries = _parse_streams_page(resp.text)
    except Exception as e:
        logger.warning(f"YouTube stream fetch error: {e}")

    if not entries:
        # Резерв из базы данных: последнее активное служение или видео с YouTube
        db_vids = Video.objects.filter(is_active=True, youtube_url__isnull=False).exclude(youtube_url='').order_by('-created_at')[:5]
        for dv in db_vids:
            vid_id = dv.get_youtube_id()
            if vid_id:
                is_st = any(kw.upper() in dv.title.upper() for kw in STREAM_KEYWORDS)
                entries.append({
                    'video_id': vid_id,
                    'title': dv.title,
                    'published': str(dv.created_at),
                    'is_stream': is_st,
                })

    if not entries:
        fallback = {'video_id': None, 'error': 'Видео не найдены', 'platform': 'youtube'}
        cache.set('yt_stream_cache', fallback, 60)
        return JsonResponse(fallback, status=404)

    stream_entries = [e for e in entries if e['is_stream']]
    best = stream_entries[0] if stream_entries else entries[0]
    is_live = is_stream_live()
    payload = {
        'video_id': best['video_id'],
        'title': best['title'],
        'published': best['published'],
        'is_stream': best['is_stream'],
        'is_live': is_live,
        'platform': 'youtube',
        'channel_handle': YT_CHANNEL_HANDLE,
        'all_streams': stream_entries[:5] if stream_entries else entries[:5],
    }
    cache.set('yt_stream_cache', payload, 300)
    return JsonResponse(payload)

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
@staff_member_required
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

MONTH_NAMES_RU = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
    5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
    9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
}
WEEKDAY_NAMES_RU = {
    0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'
}

def _get_calendar_events_context():
    """Возвращает форматированный список событий и список активных месяцев для календаря"""
    now = timezone.now()
    raw_events = list(Event.objects.filter(
        is_active=True
    ).filter(
        models.Q(end_date__gte=now - timedelta(days=1)) | 
        (models.Q(end_date__isnull=True) & models.Q(start_date__gte=now - timedelta(days=1)))
    ).order_by('start_date')[:50])

    if len(raw_events) < 4:
        raw_events = list(Event.objects.filter(is_active=True).order_by('start_date')[:20])

    events_list = []
    months_seen = {}

    for ev in raw_events:
        dt_local = ev.start_date.astimezone(KRA_TZ)
        m_num = dt_local.month
        m_name = MONTH_NAMES_RU.get(m_num, '')
        m_key = f"{dt_local.year}-{m_num:02d}"
        if m_key not in months_seen:
            months_seen[m_key] = {
                'key': m_key,
                'name': m_name,
                'year': dt_local.year,
                'label': f"{m_name} {dt_local.year}"
            }

        title_lower = ev.title.lower()
        if ev.is_conference:
            cat_slug = 'conference'
            cat_label = 'Конференция'
            cat_color = 'amber'
        elif 'богослужение' in title_lower or 'служение' in title_lower:
            cat_slug = 'worship'
            cat_label = 'Богослужение'
            cat_color = 'emerald'
        elif 'молитв' in title_lower:
            cat_slug = 'prayer'
            cat_label = 'Молитва'
            cat_color = 'purple'
        elif 'молод' in title_lower or 'youth' in title_lower:
            cat_slug = 'youth'
            cat_label = 'Молодёжное'
            cat_color = 'cyan'
        elif 'альфа' in title_lower or 'курс' in title_lower or 'школа' in title_lower:
            cat_slug = 'course'
            cat_label = 'Курс / Обучение'
            cat_color = 'blue'
        else:
            cat_slug = 'event'
            cat_label = 'Событие'
            cat_color = 'amber'

        desc = ev.description or ''
        short_desc = desc[:120] + '...' if len(desc) > 120 else desc

        events_list.append({
            'id': ev.id,
            'title': ev.title,
            'slug': ev.slug,
            'description': desc,
            'short_description': getattr(ev, 'short_description', '') or short_desc,
            'start_date': ev.start_date.isoformat(),
            'month_key': m_key,
            'month_name': m_name,
            'year': dt_local.year,
            'month': dt_local.month,
            'day': dt_local.day,
            'iso_date': dt_local.strftime('%Y-%m-%d'),
            'weekday': WEEKDAY_NAMES_RU.get(dt_local.weekday(), ''),
            'time_str': dt_local.strftime('%H:%M'),
            'location': ev.location,
            'address': ev.address,
            'is_conference': getattr(ev, 'is_conference', False),
            'is_online': getattr(ev, 'is_online', False),
            'badge': getattr(ev, 'badge', '') or cat_label,
            'cat_slug': cat_slug,
            'cat_label': cat_label,
            'cat_color': cat_color,
            'image_url': ev.image.url if ev.image else None,
            'has_registration': hasattr(ev, 'is_registration_open') and ev.is_registration_open,
        })

    return {
        'calendar_events': events_list,
        'calendar_months': list(months_seen.values()),
        'calendar_events_json': _json.dumps(events_list, default=str, ensure_ascii=False),
    }

def home(request):
    """Главная страница с таймером воскресной трансляции и интерактивным календарем"""
    from .services_video_sync import trigger_background_auto_sync
    trigger_background_auto_sync()

    current_announcement = Announcement.objects.filter(
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).first()
    time_info = get_time_until_service()
    now = timezone.now()
    featured_events = Event.objects.filter(
        is_active=True, 
        is_featured=True
    ).filter(
        models.Q(end_date__gte=now) | (models.Q(end_date__isnull=True) & models.Q(start_date__gte=now))
    ).order_by('start_date')[:10]
    hero_backgrounds = HeroBackground.objects.filter(is_active=True).order_by('order', '-created_at')[:5]
    
    server_now_ms = int(timezone.now().timestamp() * 1000)

    news = News.objects.filter(
        is_active=True
    ).order_by('-is_featured', '-created_at')[:6]

    podcast_episodes = PodcastEpisode.objects.filter(is_active=True).order_by('order')[:25]
    calendar_data = _get_calendar_events_context()
    
    context = {
        'announcement': current_announcement,
        'show_announcement': current_announcement is not None,
        'user': request.user,
        'time_until_service': time_info,
        'is_live': time_info['is_live'],
        'service_schedule': SCHEDULE,
        'featured_events': featured_events,
        'hero_backgrounds': hero_backgrounds,
        'server_now_ms': server_now_ms,
        'server_now_kra': _kra_now().isoformat(),
        'news': news,
        'podcast_episodes': podcast_episodes,
        'calendar_events': calendar_data['calendar_events'],
        'calendar_months': calendar_data['calendar_months'],
        'calendar_events_json': calendar_data['calendar_events_json'],
    }
    return render(request, 'home.html', context)

def offline_view(request):
    """Страница при отсутствии интернета"""
    return render(request, 'offline.html')

def register_view(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = RegisterForm(request.POST, request=request)
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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import UserBibleProgress, PrayerRequest, EventRegistration, BiblePlan, User
import json

@login_required
def profile_view(request):
    """Личный кабинет пользователя с полным обзором духовной активности"""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Молитвенная активность
    user_prayers = PrayerRequest.objects.filter(user=user).order_by('-created_at')
    total_prayers = user_prayers.count()
    answered_prayers_count = user_prayers.filter(is_answered=True).count()
    active_prayers_count = user_prayers.filter(is_answered=False).count()
    
    # Сколько людей молятся за пользователя
    praying_for_user_count = user_prayers.aggregate(s=models.Sum('prayer_count'))['s'] or 0
    
    # За скольких людей молится пользователь
    user_praying_for_others_count = user.supported_prayers.count()
    
    # Откровения и свидетельства пользователя
    user_revelations = Revelation.objects.filter(user=user).order_by('-created_at')
    revelations_count = user_revelations.count()
    
    # Суммарные реакции на свидетельства пользователя
    user_rev_ids = list(user_revelations.values_list('id', flat=True))
    reaction_totals = {'total': 0, 'amen': 0, 'glory': 0, 'fire': 0, 'grace': 0}
    if user_rev_ids:
        all_reactions = RevelationReaction.objects.filter(revelation_id__in=user_rev_ids)
        reaction_totals['total'] = all_reactions.count()
        if reaction_totals['total'] > 0:
            counts = all_reactions.values('reaction_type').annotate(c=Count('id'))
            for item in counts:
                reaction_totals[item['reaction_type']] = item['c']
    
    # Любимые стихи из Библии
    favorite_verses = FavoriteVerse.objects.filter(user=user).order_by('-created_at')
    
    # Молитвенные друзья (система взаимной дружбы и молитвы)
    following_conns = list(PrayerConnection.objects.filter(from_user=user).select_related('to_user', 'to_user__profile'))
    follower_conns = list(PrayerConnection.objects.filter(to_user=user).select_related('from_user', 'from_user__profile'))
    
    following_map = {c.to_user_id: c for c in following_conns}
    follower_map = {c.from_user_id: c for c in follower_conns}
    
    following_ids = set(following_map.keys())
    follower_ids = set(follower_map.keys())
    
    # Взаимные молитвенные друзья (оба молятся друг за друга)
    mutual_friend_ids = following_ids.intersection(follower_ids)
    mutual_friends = [following_map[uid].to_user for uid in mutual_friend_ids]
    
    # Я молюсь (но они пока не молятся в ответ)
    only_following = [following_map[uid].to_user for uid in (following_ids - mutual_friend_ids)]
    
    # Молятся за меня (я еще не молюсь в ответ -> кнопка «Молиться в ответ»)
    only_followers = [follower_map[uid].from_user for uid in (follower_ids - mutual_friend_ids)]
    
    # Регистрации на события и конференции
    from django.db.models import Q
    registered_events = EventRegistration.objects.filter(
        Q(user=user) | (Q(email__iexact=user.email) & ~Q(email=''))
    ).select_related('event').distinct().order_by('-registered_at')
    
    # Заявки на служение
    ministry_applications = MinistryApplication.objects.filter(user=user).select_related('ministry').order_by('-created_at')

    # Стих дня (100% синхронизирован с Библиотекой)
    daily_verse = DailyVerse.get_today_verse()
    is_daily_saved = False
    if daily_verse:
        is_daily_saved = favorite_verses.filter(reference=daily_verse.reference).exists()
    
    context = {
        'user': user,
        'profile': profile,
        'user_prayers': user_prayers,
        'total_prayers': total_prayers,
        'answered_prayers_count': answered_prayers_count,
        'active_prayers_count': active_prayers_count,
        'praying_for_user_count': praying_for_user_count,
        'user_praying_for_others_count': user_praying_for_others_count,
        'user_revelations': user_revelations,
        'revelations_count': revelations_count,
        'reaction_totals': reaction_totals,
        'favorite_verses': favorite_verses,
        'favorite_verses_count': favorite_verses.count(),
        'mutual_friends': mutual_friends,
        'mutual_friends_count': len(mutual_friends),
        'only_following': only_following,
        'only_followers': only_followers,
        'following_conns': following_conns,
        'follower_conns': follower_conns,
        'friends_count': len(mutual_friends),
        'total_followers_count': len(follower_conns),
        'total_following_count': len(following_conns),
        'registered_events': registered_events,
        'events_count': registered_events.count(),
        'ministry_applications': ministry_applications,
        'ministry_applications_count': ministry_applications.count(),
        'daily_verse': daily_verse,
        'is_daily_saved': is_daily_saved,
    }
    return render(request, 'profile.html', context)

@login_required
def profile_edit_view(request):
    """Редактирование профиля, аватара и социальных сетей"""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES)
        if form.is_valid():
            # Обновление аватара
            if form.cleaned_data.get('delete_avatar'):
                if profile.avatar:
                    profile.avatar.delete(save=False)
                    profile.avatar = None
            elif 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']

            # Обновление User
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Обновление UserProfile
            profile.phone = form.cleaned_data['phone']
            profile.telegram = form.cleaned_data['telegram']
            profile.vk = form.cleaned_data['vk']
            profile.city = form.cleaned_data['city']
            profile.home_group = form.cleaned_data['home_group']
            profile.baptism_date = form.cleaned_data['baptism_date']
            profile.bio = form.cleaned_data['bio']
            profile.is_public = form.cleaned_data['is_public']
            profile.notify_daily_verse = form.cleaned_data['notify_daily_verse']
            profile.notify_prayer_answers = form.cleaned_data['notify_prayer_answers']
            profile.notify_events = form.cleaned_data['notify_events']
            profile.save()
            
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = ProfileEditForm(initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': profile.phone,
            'telegram': profile.telegram,
            'vk': profile.vk,
            'city': profile.city,
            'home_group': profile.home_group,
            'baptism_date': profile.baptism_date,
            'bio': profile.bio,
            'is_public': profile.is_public,
            'notify_daily_verse': profile.notify_daily_verse,
            'notify_prayer_answers': profile.notify_prayer_answers,
            'notify_events': profile.notify_events,
        })
    return render(request, 'profile_edit.html', {'user': user, 'profile': profile, 'form': form})


@login_required
def profile_avatar_upload(request):
    """AJAX эндпоинт быстрой загрузки / удаления аватара прямо со страницы профиля"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)
    
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.POST.get('delete') == '1':
        if profile.avatar:
            profile.avatar.delete(save=False)
            profile.avatar = None
            profile.save()
        return JsonResponse({
            'success': True, 
            'avatar_url': None, 
            'initials': profile.get_initials(), 
            'message': 'Фото профиля удалено'
        })
    
    avatar_file = request.FILES.get('avatar')
    if not avatar_file:
        return JsonResponse({'success': False, 'error': 'Файл не выбран'}, status=400)
    
    # Ограничение размера файла (макс. 10MB)
    if avatar_file.size > 10 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'Файл слишком большой (максимум 10 МБ)'}, status=400)
    
    # Сохраняем фото
    if profile.avatar:
        profile.avatar.delete(save=False)
    profile.avatar = avatar_file
    profile.save()
    
    return JsonResponse({
        'success': True,
        'avatar_url': profile.get_avatar_url(),
        'message': 'Фото профиля успешно обновлено!'
    })


def user_public_profile(request, username):
    """Публичный профиль прихожанина церкви"""
    target_user = get_object_or_404(User, username=username)
    
    # Если текущий пользователь открывает свой собственный профиль — перенаправляем в личный кабинет
    if request.user.is_authenticated and request.user == target_user:
        return redirect('profile')
        
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    
    # Проверяем, молится ли текущий пользователь за этого человека (молитвенная связь)
    is_prayer_friend = False
    target_prays_for_me = False
    is_mutual = False
    if request.user.is_authenticated:
        is_prayer_friend = PrayerConnection.objects.filter(from_user=request.user, to_user=target_user).exists()
        target_prays_for_me = PrayerConnection.objects.filter(from_user=target_user, to_user=request.user).exists()
        is_mutual = is_prayer_friend and target_prays_for_me
            
    # Открытые молитвенные нужды этого пользователя
    public_prayers = PrayerRequest.objects.filter(user=target_user, is_public=True, is_anonymous=False).order_by('-created_at')
    
    # Открытые свидетельства и откровения этого пользователя
    public_revelations = Revelation.objects.filter(user=target_user, is_public=True, is_anonymous=False).order_by('-created_at')
    
    # Любимые стихи Писания
    favorite_verses = FavoriteVerse.objects.filter(user=target_user).order_by('-created_at')
    
    # Статистика
    prayers_count = public_prayers.count()
    revelations_count = public_revelations.count()
    followers_count = PrayerConnection.objects.filter(to_user=target_user).count()
    
    # Идентификаторы молитв, за которые уже молится текущий пользователь
    supported_prayer_ids = set()
    if request.user.is_authenticated:
        supported_prayer_ids = set(request.user.supported_prayers.values_list('id', flat=True))
    
    context = {
        'target_user': target_user,
        'profile': profile,
        'is_prayer_friend': is_prayer_friend,
        'target_prays_for_me': target_prays_for_me,
        'is_mutual': is_mutual,
        'public_prayers': public_prayers,
        'public_revelations': public_revelations,
        'favorite_verses': favorite_verses,
        'prayers_count': prayers_count,
        'revelations_count': revelations_count,
        'followers_count': followers_count,
        'supported_prayer_ids': supported_prayer_ids,
    }
    return render(request, 'user_profile.html', context)


@login_required
@require_POST
def toggle_prayer_friend(request, username):
    """Добавить или удалить из молитвенных друзей («Молиться вместе»)"""
    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        return JsonResponse({'success': False, 'error': 'Нельзя добавить самого себя'}, status=400)
        
    target_name = target_user.first_name or target_user.username
    target_prays_for_me = PrayerConnection.objects.filter(from_user=target_user, to_user=request.user).exists()

    conn = PrayerConnection.objects.filter(from_user=request.user, to_user=target_user).first()
    if conn:
        conn.delete()
        is_following = False
        message = f'Вы перестали молиться за {target_name}'
    else:
        PrayerConnection.objects.create(from_user=request.user, to_user=target_user)
        is_following = True
        if target_prays_for_me:
            message = f'Слава Богу! Теперь вы и {target_name} — взаимные молитвенные друзья! 🤝'
        else:
            message = f'Слава Богу! Вы начали молиться за {target_name}! 🙏'
        
    # Проверяем взаимность
    is_mutual = target_prays_for_me and is_following
    followers_count = PrayerConnection.objects.filter(to_user=target_user).count()
    
    return JsonResponse({
        'success': True,
        'is_following': is_following,
        'is_mutual': is_mutual,
        'target_prays_for_me': target_prays_for_me,
        'followers_count': followers_count,
        'message': message
    })


@login_required
@require_POST
def add_favorite_verse(request):
    """Добавление стиха в избранное (из Стиха дня или вручную)"""
    try:
        if request.content_type == 'application/json':
            data = _json.loads(request.body)
            reference = data.get('reference', '').strip()
            verse_text = data.get('verse_text', '').strip()
            note = data.get('note', '').strip()
        else:
            reference = request.POST.get('reference', '').strip()
            verse_text = request.POST.get('verse_text', '').strip()
            note = request.POST.get('note', '').strip()
            
        if not reference or not verse_text:
            return JsonResponse({'success': False, 'error': 'Укажите место Писания и текст стиха'}, status=400)
            
        verse, created = FavoriteVerse.objects.get_or_create(
            user=request.user,
            reference=reference,
            defaults={'verse_text': verse_text, 'note': note}
        )
        if not created and note:
            verse.note = note
            verse.save()
            
        return JsonResponse({
            'success': True,
            'created': created,
            'id': verse.id,
            'reference': verse.reference,
            'verse_text': verse.verse_text,
            'message': 'Стих сохранен в ваш профиль!' if created else 'Стих уже сохранен в профиле'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def delete_favorite_verse(request, verse_id):
    """Удаление стиха из избранного"""
    verse = get_object_or_404(FavoriteVerse, id=verse_id, user=request.user)
    ref = verse.reference
    verse.delete()
    return JsonResponse({'success': True, 'message': f'Стих {ref} удален из профиля'})


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

@staff_member_required
def upload_pastor_photo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    photo = request.FILES.get('photo')
    pastor = request.POST.get('pastor')
    
    if not photo or not pastor:
        return JsonResponse({'error': 'Missing data'}, status=400)
    
    # Сохраняем файл
    ext = os.path.splitext(photo.name)[1]
    filename = f'pastors/{pastor}{ext}'
    path = default_storage.save(filename, ContentFile(photo.read()))
    
    # Возвращаем URL
    return JsonResponse({
        'success': True,
        'photo_url': default_storage.url(path)
    })

from django.shortcuts import render
from .models import PastorPhoto

def about_view(request):
    pastor_photos = {}
    pastor_slugs = ['ashaev', 'zyryanov', 'yunyushkin', 'pritchin', 'kononov', 'schmidt', 'plotnikov', 'buchenik']
    
    # Получаем фото из базы данных
    for slug in pastor_slugs:
        try:
            pastor = PastorPhoto.objects.get(slug=slug)
            if pastor.image:
                pastor_photos[slug] = pastor.image.url
        except PastorPhoto.DoesNotExist:
            pass
            
    return render(request, 'info/about.html', {'pastor_photos': pastor_photos})

from .models import HomeGroup

def home_meet_view(request):
    """Страница домашних встреч с интерактивным подбором по районам и картой"""
    districts = HomeGroup.objects.filter(is_active=True).values_list('district', flat=True).distinct()
    
    groups_by_district = {}
    groups_all_list = []
    
    for district in districts:
        district_groups = HomeGroup.objects.filter(
            is_active=True,
            district=district
        ).order_by('order', 'address')
        groups_by_district[district] = district_groups
        
        for g in district_groups:
            groups_all_list.append({
                'id': g.id,
                'district': g.district,
                'address': g.address,
                'leader_name': g.leader_name or '',
                'leader_phone': g.leader_phone or '',
                'leader_telegram': g.leader_telegram or '',
                'day': g.get_day_display(),
                'time': g.time or '',
                'type': g.get_type_display(),
                'type_slug': g.group_type,
                'age': g.get_age_display(),
                'description': g.description or '',
                'lat': g.latitude,
                'lng': g.longitude,
            })
            
    user_initials = {}
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user_initials = {
            'name': profile.get_display_name() if hasattr(profile, 'get_display_name') else (request.user.get_full_name() or request.user.username),
            'phone': profile.phone or '',
            'telegram': profile.telegram or '',
            'email': request.user.email or '',
        }

    context = {
        'groups_by_district': groups_by_district,
        'districts': districts,
        'groups_json': _json.dumps(groups_all_list, ensure_ascii=False),
        'total_groups': len(groups_all_list),
        'user_initials': user_initials,
        'title': 'Домашние группы — KCLC',
    }
    return render(request, 'info/home_meet.html', context)


def calendar_page_view(request):
    """Отдельная страница полного интерактивного календаря событий и служений"""
    cal_data = _get_calendar_events_context()
    context = {
        'title': 'Календарь событий и служений — KCLC',
        **cal_data,
    }
    return render(request, 'info/calendar.html', context)


def ministries_list_view(request):
    """Каталог церковных служений (Хочу служить)"""
    ministries = Ministry.objects.filter(is_active=True).order_by('order', 'title')
    
    user_initials = {}
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user_initials = {
            'name': profile.get_display_name() if hasattr(profile, 'get_display_name') else (request.user.get_full_name() or request.user.username),
            'phone': profile.phone or '',
            'telegram': profile.telegram or '',
            'email': request.user.email or '',
        }
        
    context = {
        'ministries': ministries,
        'user_initials': user_initials,
        'title': 'Хочу служить — Команды церкви KCLC',
    }
    return render(request, 'info/ministries.html', context)


def ministry_detail_view(request, slug):
    """Детальная страница служения церкви"""
    ministry = get_object_or_404(Ministry, slug=slug, is_active=True)
    other_ministries = Ministry.objects.filter(is_active=True).exclude(id=ministry.id).order_by('order')[:3]
    
    user_initials = {}
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user_initials = {
            'name': profile.get_display_name() if hasattr(profile, 'get_display_name') else (request.user.get_full_name() or request.user.username),
            'phone': profile.phone or '',
            'telegram': profile.telegram or '',
            'email': request.user.email or '',
        }
        
    context = {
        'ministry': ministry,
        'other_ministries': other_ministries,
        'user_initials': user_initials,
        'title': f'{ministry.title} — Служение церкви KCLC',
    }
    return render(request, 'info/ministry_detail.html', context)


@require_POST
def apply_ministry_api(request, slug):
    """API подачи заявки в команду служения с сохранением в БД"""
    ministry = get_object_or_404(Ministry, slug=slug, is_active=True)
    
    if request.content_type == 'application/json':
        try:
            data = _json.loads(request.body)
        except Exception:
            return JsonResponse({'success': False, 'error': 'Некорректный JSON'}, status=400)
    else:
        data = request.POST

    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    telegram = data.get('telegram', '').strip()
    email = data.get('email', '').strip()
    message = data.get('message', '').strip()

    if not name:
        return JsonResponse({'success': False, 'error': 'Пожалуйста, укажите ваше имя'}, status=400)
    if not phone:
        return JsonResponse({'success': False, 'error': 'Пожалуйста, укажите контактный телефон'}, status=400)

    user = request.user if request.user.is_authenticated else None

    application = MinistryApplication.objects.create(
        ministry=ministry,
        user=user,
        name=name,
        phone=phone,
        telegram=telegram,
        email=email,
        message=message,
        status='new'
    )

    if user:
        try:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            changed = False
            if not profile.phone and phone:
                profile.phone = phone
                changed = True
            if not profile.telegram and telegram:
                profile.telegram = telegram
                changed = True
            if changed:
                profile.save()
        except Exception as e:
            logger.warning(f"Не удалось обновить профиль пользователя: {e}")

    return JsonResponse({
        'success': True,
        'message': f'Спасибо, {name}! Ваша заявка в команду «{ministry.title}» принята. Лидер служения свяжется с вами!',
        'application_id': application.id,
    })


def community_map_view(request):
    """Интерактивная карта: центральная церковь, залы, домашние группы, филиалы и события"""
    from church_app.services_geo import get_all_map_locations, CENTRAL_CHURCH, REGIONAL_BRANCHES
    
    locations = get_all_map_locations(include_homegroups=True, include_events=True)
    homegroups_count = HomeGroup.objects.filter(is_active=True).count()
    branches_count = len(REGIONAL_BRANCHES)
    events_count = Event.objects.filter(is_active=True).exclude(latitude__isnull=True).count()
    
    context = {
        'title': 'Интерактивная карта — KCLC',
        'locations_json': _json.dumps(locations, ensure_ascii=False),
        'total_locations': len(locations),
        'homegroups_count': homegroups_count,
        'branches_count': branches_count,
        'events_count': events_count,
        'central_church': CENTRAL_CHURCH,
    }
    return render(request, 'info/community_map.html', context)


@require_GET
def api_map_locations(request):
    """JSON API со всеми локациями карты"""
    from church_app.services_geo import get_all_map_locations
    return JsonResponse({'locations': get_all_map_locations()})


def regional_churches_view(request):
    """Страница дочерних и региональных церквей по всей России"""
    from church_app.services_geo import REGIONAL_BRANCHES
    return render(request, 'info/regional_churches.html', {
        'title': 'Церкви в других городах — KCLC',
        'branches': REGIONAL_BRANCHES,
        'total_count': len(REGIONAL_BRANCHES),
    })