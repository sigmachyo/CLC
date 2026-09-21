from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from .models import Category, Video, BiblePlan, BibleReading, UserBibleProgress, Event, EventRegistration, KidsContent, KidsProgress, DailyVerse, PodcastEpisode
from .forms import ConferenceRegistrationForm
from .services_email import send_conference_registration_email
import json

def library_home(request):
    """Главная страница библиотеки"""
    categories = Category.objects.filter(is_active=True).order_by('order')
    recent_videos = Video.objects.filter(is_active=True).exclude(category__slug='proslavlenie').select_related('category')[:8]
    worship_songs = Video.objects.filter(category__slug='proslavlenie', is_active=True).select_related('category')[:8]
    podcast_episodes = PodcastEpisode.objects.filter(is_active=True).order_by('order')[:25]
    
    today = timezone.localdate()
    day_of_year = today.toordinal()
    
    # 1. Background Logic (Локальные высококачественные фоны без зависимости от Unsplash и VPN)
    from .daily_verse_data import VERSES
    verse_bg_num = (day_of_year % 31) + 1
    daily_bg_url = f"/static/img/daily_verses/verse_{verse_bg_num}.jpg"
    
    # 2. Verse Logic
    daily_verse = DailyVerse.get_today_verse()
    
    context = {
        'categories': categories,
        'recent_videos': recent_videos,
        'worship_songs': worship_songs,
        'podcast_episodes': podcast_episodes,
        'daily_verse': daily_verse,
        'daily_bg_url': daily_bg_url,
    }

    return render(request, 'library/home.html', context)
def library_category(request, category_slug):
    """Страница категории"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    context = {'category': category}
    if category.category_type == 'video':
        videos = Video.objects.filter(category=category, is_active=True).order_by('-is_featured', '-created_at')
        context['videos'] = videos
        return render(request, 'library/category_video.html', context)
    elif category.category_type == 'bible':
        return redirect('library_home')
    elif category.category_type == 'events':
        now = timezone.now()
        upcoming_events = Event.objects.filter(is_active=True).filter(
            Q(end_date__gte=now) | (Q(end_date__isnull=True) & Q(start_date__gte=now))
        ).order_by('start_date')
        past_events = Event.objects.filter(is_active=True).filter(
            Q(end_date__lt=now) | (Q(end_date__isnull=True) & Q(start_date__lt=now))
        ).order_by('-start_date')
        context['upcoming_events'] = upcoming_events
        context['past_events'] = past_events
        context['events'] = upcoming_events
        return render(request, 'library/category_events.html', context)
    elif category.category_type == 'kids':
        return redirect('library_home')
        
    # Default fallback
    context['items'] = []
    return render(request, 'library/category.html', context)
def video_detail(request, video_id):
    """Страница просмотра видео"""
    video = get_object_or_404(Video, id=video_id, is_active=True)
    video.increment_views()
    recommended = Video.objects.filter(
        category=video.category, 
        is_active=True
    ).exclude(id=video.id).order_by('-views_count')[:6]
    context = {
        'video': video,
        'recommended': recommended,
    }
    return render(request, 'library/video_detail.html', context)
def bible_home(request):
    """Страница чтения Библии (перенаправление, планы чтения отключены)"""
    return redirect('library_home')

def bible_plan_detail(request, plan_id):
    """Детали плана чтения (перенаправление, планы чтения отключены)"""
    return redirect('library_home')

def bible_read_day(request, plan_id, day):
    """Чтение конкретного дня (перенаправление, планы чтения отключены)"""
    return redirect('library_home')

def complete_bible_day(request, plan_id, day):
    """API для отметки дня как прочитанного (отключено)"""
    return JsonResponse({'success': False, 'message': 'Планы чтения отключены'}, status=404)
def events_list(request):
    """Список событий"""
    event_type = request.GET.get('type', '')
    month = request.GET.get('month', '')
    events = Event.objects.filter(is_active=True)
    if event_type:
        events = events.filter(event_type=event_type)
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            events = events.filter(
                start_date__year=year,
                start_date__month=month_num
            )
        except (ValueError, TypeError):
            pass
    now = timezone.now()
    upcoming_events = events.filter(
        Q(end_date__gte=now) | (Q(end_date__isnull=True) & Q(start_date__gte=now))
    ).order_by('start_date')
    past_events = events.filter(
        Q(end_date__lt=now) | (Q(end_date__isnull=True) & Q(start_date__lt=now))
    ).order_by('-start_date')[:12]
    from django.db.models.functions import TruncMonth
    from django.db.models import Count
    months = events.annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    context = {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'months': months,
        'current_filter': {
            'type': event_type,
            'month': month,
        }
    }
    return render(request, 'library/events_list.html', context)
def event_detail(request, slug):
    """Детали события или сложный лендинг конференции"""
    event = get_object_or_404(Event, slug=slug, is_active=True)
    
    # Проверяем, есть ли у события блоки конструктора лендингов
    blocks = event.blocks.filter(is_active=True).order_by('order')
    is_conference_landing = event.is_conference or blocks.exists()

    user_registration = None
    if request.user.is_authenticated:
        user_registration = EventRegistration.objects.filter(event=event, user=request.user).first()

    if is_conference_landing:
        # Предзаполнение формы регистрации из профиля
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['first_name'] = request.user.first_name
            initial_data['last_name'] = request.user.last_name
            initial_data['email'] = request.user.email
            if hasattr(request.user, 'profile'):
                p = request.user.profile
                initial_data['phone'] = p.phone or ''
                initial_data['telegram'] = p.telegram or ''

        form = ConferenceRegistrationForm(initial=initial_data)

        # Карта блоков по типу для быстрого доступа в шаблоне
        blocks_by_type = {}
        for b in blocks:
            blocks_by_type[b.block_type] = b.content

        context = {
            'event': event,
            'blocks': blocks,
            'blocks_by_type': blocks_by_type,
            'user_registration': user_registration,
            'is_registered': bool(user_registration),
            'form': form,
        }
        return render(request, 'events/conference_landing.html', context)

    # Обычное простое событие
    similar_events = Event.objects.filter(
        event_type=event.event_type,
        is_active=True
    ).exclude(id=event.id).order_by('start_date')[:3]

    context = {
        'event': event,
        'user_registration': user_registration,
        'similar_events': similar_events,
    }
    return render(request, 'library/event_detail.html', context)


def event_register(request, slug):
    """Регистрация на событие или конференцию с чеком пожертвования и квитанцией"""
    event = get_object_or_404(Event, slug=slug, is_active=True)
    
    if request.method == 'POST':
        # Проверка лимита участников
        if event.max_participants > 0 and event.registrations.count() >= event.max_participants:
            messages.error(request, 'К сожалению, достигнут лимит участников на это событие.')
            return redirect('event_detail', slug=event.slug)

        form = ConferenceRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data['first_name'].strip()
            last_name = form.cleaned_data['last_name'].strip()
            email = form.cleaned_data['email'].strip().lower()
            phone = form.cleaned_data['phone'].strip()
            telegram = form.cleaned_data.get('telegram', '').strip()
            payment_receipt = form.cleaned_data.get('payment_receipt')

            user = request.user if request.user.is_authenticated else None

            # Проверка существующей регистрации (по пользователю или email)
            existing = None
            if user:
                existing = EventRegistration.objects.filter(event=event, user=user).first()
            if not existing and email:
                existing = EventRegistration.objects.filter(event=event, email__iexact=email).first()

            if existing:
                # Если уже был зарегистрирован, но досылает чек
                if payment_receipt and not existing.payment_receipt:
                    existing.payment_receipt = payment_receipt
                    existing.payment_status = 'pending'
                    existing.save()
                    messages.success(request, 'Чек успешно прикреплен к вашей регистрации!')
                else:
                    messages.info(request, f'Вы уже зарегистрированы на это событие! Номер вашего билета: {existing.ticket_number}')
                
                return render(request, 'events/registration_success.html', {
                    'event': event,
                    'registration': existing,
                    'already_registered': True,
                })

            # Создание новой регистрации
            status = 'pending' if payment_receipt else ('free' if not event.registration_fee else 'pending')
            registration = EventRegistration.objects.create(
                event=event,
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                telegram=telegram,
                payment_receipt=payment_receipt,
                payment_status=status,
                is_confirmed=(status == 'free'),
            )

            # Обновление контактов в профиле пользователя, если они не были заполнены
            if user and hasattr(user, 'profile'):
                p = user.profile
                changed = False
                if not p.phone and phone:
                    p.phone = phone
                    changed = True
                if not p.telegram and telegram:
                    p.telegram = telegram
                    changed = True
                if not user.first_name and first_name:
                    user.first_name = first_name
                    user.save()
                if not user.last_name and last_name:
                    user.last_name = last_name
                    user.save()
                if changed:
                    p.save()

            # Отправка электронного билета и квитанции на email
            send_conference_registration_email(registration, request.get_host())

            messages.success(request, f'Регистрация успешно завершена! Ваш билет: {registration.ticket_number}')
            return render(request, 'events/registration_success.html', {
                'event': event,
                'registration': registration,
                'already_registered': False,
            })
        else:
            # Ошибки формы
            messages.error(request, 'Пожалуйста, проверьте правильность заполнения формы регистрации.')
            # Повторный рендеринг лендинга с ошибками
            blocks = event.blocks.filter(is_active=True).order_by('order')
            blocks_by_type = {b.block_type: b.content for b in blocks}
            return render(request, 'events/conference_landing.html', {
                'event': event,
                'blocks': blocks,
                'blocks_by_type': blocks_by_type,
                'form': form,
                'scroll_to_reg': True,
            })

    return redirect('event_detail', slug=event.slug)
def kids_home(request):
    """Детская страница"""
    content_type = request.GET.get('type', '')
    age_group = request.GET.get('age', '')
    content = KidsContent.objects.filter(is_active=True)
    if content_type:
        content = content.filter(content_type=content_type)
    if age_group:
        content = content.filter(age_group=age_group)
    featured = content.filter(is_featured=True).order_by('-created_at')[:6]
    cartoons = content.filter(content_type='cartoon').order_by('-created_at')[:8]
    lessons = content.filter(content_type='lesson').order_by('-created_at')[:8]
    games = content.filter(content_type='game').order_by('-created_at')[:6]
    if request.user.is_authenticated:
        user_progress = {p.content_id: p for p in KidsProgress.objects.filter(user=request.user)}
        for item in content:
            item.user_progress = user_progress.get(item.id)
    context = {
        'featured': featured,
        'cartoons': cartoons,
        'lessons': lessons,
        'games': games,
        'content_types': KidsContent.CONTENT_TYPES,
        'age_groups': KidsContent.AGE_GROUPS,
        'filters': {
            'type': content_type,
            'age': age_group,
        }
    }
    return render(request, 'library/kids_home.html', context)
def kids_content_detail(request, content_id):
    """Детальная страница детского контента"""
    content = get_object_or_404(KidsContent, id=content_id, is_active=True)
    content.increment_views()
    if request.user.is_authenticated:
        progress, created = KidsProgress.objects.get_or_create(
            user=request.user,
            content=content
        )
        if request.method == 'POST' and 'complete' in request.POST:
            progress.completed = True
            progress.completed_at = timezone.now()
            if 'score' in request.POST:
                progress.score = int(request.POST.get('score', 0))
            progress.save()
            messages.success(request, 'Отлично! Ты молодец!')
            return redirect('kids_content_detail', content_id=content.id)
    else:
        progress = None
    similar = KidsContent.objects.filter(
        content_type=content.content_type,
        age_group=content.age_group,
        is_active=True
    ).exclude(id=content.id).order_by('-created_at')[:4]
    context = {
        'content': content,
        'progress': progress,
        'similar': similar,
    }
    template_map = {
        'cartoon': 'library/kids_cartoon.html',
        'lesson': 'library/kids_lesson.html',
        'game': 'library/kids_game.html',
        'craft': 'library/kids_craft.html',
        'song': 'library/kids_song.html',
    }
    return render(request, template_map.get(content.content_type, 'library/kids_detail.html'), context)

def video_list(request):
    """Страница со всеми видео (плейлисты: воскресные служения, проповеди, конференции)"""
    playlist = request.GET.get('playlist', 'all').strip()
    q = request.GET.get('q', '').strip()

    # Исключаем прославление из общего каталога видео, так как для него есть отдельный раздел
    base_qs = Video.objects.filter(is_active=True).exclude(category__slug='proslavlenie').select_related('category')

    if playlist == 'services':
        videos = base_qs.filter(Q(category__slug='voskresnye-sluzheniya') | Q(title__icontains='служение') | Q(title__icontains='наделение'))
    elif playlist == 'sermons':
        videos = base_qs.filter(category__slug='propovedi')
    elif playlist == 'conferences':
        videos = base_qs.filter(Q(category__slug='konferencii') | Q(title__icontains='конференция') | Q(title__icontains='семинар') | Q(title__icontains='два источника'))
    else:
        playlist = 'all'
        videos = base_qs

    if q:
        videos = videos.filter(Q(title__icontains=q) | Q(description__icontains=q))

    counts = {
        'all': base_qs.count(),
        'services': base_qs.filter(Q(category__slug='voskresnye-sluzheniya') | Q(title__icontains='служение') | Q(title__icontains='наделение')).count(),
        'sermons': base_qs.filter(category__slug='propovedi').count(),
        'conferences': base_qs.filter(Q(category__slug='konferencii') | Q(title__icontains='конференция') | Q(title__icontains='семинар') | Q(title__icontains='два источника')).count(),
    }

    context = {
        'videos': videos,
        'playlist': playlist,
        'q': q,
        'counts': counts,
    }
    return render(request, 'library/video_list.html', context)


def worship_songs_list(request):
    """Отдельная страница всех песен прославления KCLC Worship (@kclcworship) с плейлистами"""
    playlist = request.GET.get('playlist', 'all').strip()
    q = request.GET.get('q', '').strip()
    
    base_songs = Video.objects.filter(category__slug='proslavlenie', is_active=True).select_related('category')

    if playlist == 'praise':
        songs = base_songs.filter(Q(title__icontains='хвал') | Q(title__icontains='яхве') | Q(title__icontains='лев') | Q(title__icontains='башня') | Q(title__icontains='царь'))
    elif playlist == 'worship':
        songs = base_songs.filter(Q(title__icontains='поклонен') | Q(title__icontains='елей') | Q(title__icontains='тьмы') | Q(title__icontains='милости') | Q(title__icontains='иешуа'))
    elif playlist == 'acoustic':
        songs = base_songs.filter(Q(title__icontains='акусти') | Q(title__icontains='групп') | Q(title__icontains='версия'))
    elif playlist == 'covers':
        songs = base_songs.filter(Q(title__icontains='cover') | Q(title__icontains='кавер'))
    else:
        playlist = 'all'
        songs = base_songs

    if q:
        songs = songs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    all_count = base_songs.count()
    counts = {
        'all': all_count,
        'praise': base_songs.filter(Q(title__icontains='хвал') | Q(title__icontains='яхве') | Q(title__icontains='лев') | Q(title__icontains='башня') | Q(title__icontains='царь')).count(),
        'worship': base_songs.filter(Q(title__icontains='поклонен') | Q(title__icontains='елей') | Q(title__icontains='тьмы') | Q(title__icontains='милости') | Q(title__icontains='иешуа')).count(),
        'acoustic': base_songs.filter(Q(title__icontains='акусти') | Q(title__icontains='групп') | Q(title__icontains='версия')).count(),
        'covers': base_songs.filter(Q(title__icontains='cover') | Q(title__icontains='кавер')).count(),
    }

    context = {
        'songs': songs,
        'playlist': playlist,
        'q': q,
        'total_count': all_count,
        'filtered_count': songs.count(),
        'counts': counts,
    }
    return render(request, 'library/worship_list.html', context)

