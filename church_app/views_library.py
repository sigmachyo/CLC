from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from .models import Category, Video, BiblePlan, BibleReading, UserBibleProgress, Event, EventRegistration, KidsContent, KidsProgress, DailyVerse
import json
def library_home(request):
    """Главная страница библиотеки"""
    categories = Category.objects.filter(is_active=True).order_by('order')
    recent_videos = Video.objects.filter(is_active=True).order_by('-created_at')[:6]
    upcoming_events = Event.objects.filter(
        is_active=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')[:3]
    kids_content = KidsContent.objects.filter(is_active=True).order_by('-is_featured', '-created_at')[:4]
    today = timezone.localdate()
    daily_verse = (
        DailyVerse.objects.filter(date=today).first()
        or DailyVerse.objects.order_by('-date').first()
    )
    context = {
        'categories': categories,
        'recent_videos': recent_videos,
        'upcoming_events': upcoming_events,
        'kids_content': kids_content,
        'daily_verse': daily_verse,
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
        plans = BiblePlan.objects.filter(is_active=True).order_by('order')
        if request.user.is_authenticated:
            user_progress = {p.plan_id: p for p in UserBibleProgress.objects.filter(user=request.user)}
            for plan in plans:
                plan.user_progress = user_progress.get(plan.id)
                if plan.user_progress:
                    plan.progress_percentage = plan.user_progress.get_progress_percentage()
        context['plans'] = plans
        return render(request, 'library/category_bible.html', context)
    elif category.category_type == 'events':
        events = Event.objects.filter(is_active=True).order_by('start_date')
        context['events'] = events
        return render(request, 'library/category_events.html', context)
    elif category.category_type == 'kids':
        kids_content = KidsContent.objects.filter(is_active=True).order_by('-is_featured', 'order')
        context['kids_content'] = kids_content
        return render(request, 'library/category_kids.html', context)
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
    """Страница чтения Библии"""
    plans = BiblePlan.objects.filter(is_active=True).order_by('order')
    if request.user.is_authenticated:
        user_progress = {p.plan_id: p for p in UserBibleProgress.objects.filter(user=request.user)}
        for plan in plans:
            plan.user_progress = user_progress.get(plan.id)
            if plan.user_progress:
                plan.progress_percentage = plan.user_progress.get_progress_percentage()
    popular_plans = BiblePlan.objects.filter(is_active=True).annotate(
        users_count=Count('userbibleprogress')
    ).order_by('-users_count')[:3]
    context = {
        'plans': plans,
        'popular_plans': popular_plans,
    }
    return render(request, 'library/bible_home.html', context)
@login_required
def bible_plan_detail(request, plan_id):
    """Детали плана чтения"""
    plan = get_object_or_404(BiblePlan, id=plan_id, is_active=True)
    readings = plan.readings.all().order_by('day_number')
    progress, created = UserBibleProgress.objects.get_or_create(
        user=request.user,
        plan=plan
    )
    context = {
        'plan': plan,
        'readings': readings,
        'progress': progress,
    }
    return render(request, 'library/bible_plan_detail.html', context)
@login_required
def bible_read_day(request, plan_id, day):
    """Чтение конкретного дня"""
    plan = get_object_or_404(BiblePlan, id=plan_id, is_active=True)
    reading = get_object_or_404(BibleReading, plan=plan, day_number=day)
    progress = UserBibleProgress.objects.get_or_create(user=request.user, plan=plan)[0]
    if request.method == 'POST':
        progress.mark_day_completed(day)
        messages.success(request, f'День {day} отмечен как прочитанный!')
        return redirect('bible_plan_detail', plan_id=plan.id)
    context = {
        'plan': plan,
        'reading': reading,
        'progress': progress,
        'is_completed': day in progress.completed_days,
    }
    return render(request, 'library/bible_read_day.html', context)
@login_required
def complete_bible_day(request, plan_id, day):
    """API для отметки дня как прочитанного"""
    if request.method == 'POST':
        plan = get_object_or_404(BiblePlan, id=plan_id)
        progress = UserBibleProgress.objects.get_or_create(user=request.user, plan=plan)[0]
        progress.mark_day_completed(day)
        return JsonResponse({
            'success': True,
            'progress': progress.get_progress_percentage(),
            'completed_days': progress.completed_days,
        })
    return JsonResponse({'success': False}, status=400)
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
    upcoming_events = events.filter(end_date__gte=timezone.now()).order_by('start_date')
    past_events = events.filter(end_date__lt=timezone.now()).order_by('-start_date')[:6]
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
    """Детали события"""
    event = get_object_or_404(Event, slug=slug, is_active=True)
    user_registration = None
    if request.user.is_authenticated:
        user_registration = EventRegistration.objects.filter(event=event, user=request.user).first()
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
@login_required
def event_register(request, slug):
    """Регистрация на событие"""
    event = get_object_or_404(Event, slug=slug, is_active=True)
    if request.method == 'POST':
        if event.max_participants > 0 and event.registrations.count() >= event.max_participants:
            messages.error(request, 'Достигнут лимит участников')
            return redirect('event_detail', slug=event.slug)
        registration, created = EventRegistration.objects.get_or_create(
            event=event,
            user=request.user
        )
        if created:
            messages.success(request, f'Вы зарегистрированы на "{event.title}"')
        else:
            messages.info(request, 'Вы уже зарегистрированы на это событие')
        return redirect('event_detail', slug=event.slug)
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
