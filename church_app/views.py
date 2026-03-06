from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import SpiritualLevel, UserProgress, Announcement
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
import datetime
from .views_library import *

# =============================================
# 🏠 НОВАЯ ГЛАВНАЯ СТРАНИЦА - ТАЙМЕР ТРАНСЛЯЦИИ
# =============================================

def home(request):
    """Главная страница с таймером воскресной трансляции"""
    
    # Получаем прогресс пользователя для статистики в навбаре
    completed_levels = 0
    total_levels = SpiritualLevel.objects.count()
    progress_percentage = 0
    
    if request.user.is_authenticated:
        completed_levels = UserProgress.objects.filter(
            user=request.user, 
            is_completed=True
        ).count()
        if total_levels > 0:
            progress_percentage = int((completed_levels / total_levels * 100))
    
    # Получаем активное объявление (если нужно)
    current_announcement = Announcement.objects.filter(
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).first()
    
    context = {
        'completed_levels': completed_levels,
        'total_levels': total_levels,
        'progress_percentage': progress_percentage,
        'announcement': current_announcement,
        'show_announcement': current_announcement is not None,
        'user': request.user,
    }
    return render(request, 'home.html', context)


# =============================================
# 🗺️ СТРАНИЦА С КАРТОЙ УРОВНЕЙ (БЫВШАЯ ГЛАВНАЯ)
# =============================================
def index(request):
    """Страница с картой прогресса - ВСЕ УРОВНИ"""
    
    # Получаем ВСЕ уровни из базы данных
    levels = SpiritualLevel.objects.all().order_by('order')
    
    # Получаем активное объявление
    current_announcement = Announcement.objects.filter(
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).first()
    
    # Прогресс пользователя
    user_progress_dict = {}
    completed_levels = 0
    
    if request.user.is_authenticated:
        progress_entries = UserProgress.objects.filter(user=request.user)
        for progress in progress_entries:
            user_progress_dict[progress.level_id] = progress
        completed_levels = progress_entries.filter(is_completed=True).count()
    
    # СОЗДАЕМ СПИСОК УРОВНЕЙ
    city_buildings = []
    
    for level in levels:
        is_completed = False
        if level.id in user_progress_dict:
            is_completed = user_progress_dict[level.id].is_completed
        
        city_buildings.append({
            'id': level.id,
            'order': level.order,
            'title': level.title,
            'description': level.description or 'Начните свой духовный путь',
            'type': level.level_type,
            'type_display': level.get_level_type_display(),
            'building_style': level.building_style or 'church',
            'is_completed': is_completed,
            'is_available': level.is_available,
            'xp': level.order * 15,
            'position_x': 0,
            'position_y': 0,
            'height': 3,
            'color': '#3498db',
        })
    
    total_levels = len(city_buildings)
    progress_percentage = int((completed_levels / total_levels * 100)) if total_levels > 0 else 0
    
    context = {
        'city_buildings': city_buildings,
        'announcement': current_announcement,
        'show_announcement': current_announcement is not None,
        'completed_levels': completed_levels,
        'total_levels': total_levels,
        'progress_percentage': progress_percentage,
        'user': request.user,
    }
    
    return render(request, 'index.html', context)


# =============================================
# 🔐 АУТЕНТИФИКАЦИЯ
# =============================================

def register_view(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Имя пользователя уже занято')
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email уже используется')
            return redirect('register')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        login(request, user)
        messages.success(request, f'Добро пожаловать, {username}! Регистрация прошла успешно!')
        return redirect('home')  # Перенаправляем на главную с таймером
    
    return render(request, 'register.html')


def login_view(request):
    """Вход пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'С возвращением, {user.username}!')
            return redirect('home')  # Перенаправляем на главную с таймером
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    return render(request, 'login.html')


def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('home')  # Перенаправляем на главную с таймером


# =============================================
# 👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# =============================================

@login_required
def profile_view(request):
    """Страница профиля"""
    user = request.user
    
    progress_entries = UserProgress.objects.filter(user=user)
    completed_levels = progress_entries.filter(is_completed=True)
    
    total_completed = completed_levels.count()
    total_levels = SpiritualLevel.objects.count()
    progress_percentage = int((total_completed / total_levels * 100)) if total_levels > 0 else 0
    
    recent_completed = completed_levels.order_by('-completed_at')[:5]
    in_progress = progress_entries.filter(is_completed=False)[:5]
    
    context = {
        'user': user,
        'total_completed': total_completed,
        'total_levels': total_levels,
        'progress_percentage': progress_percentage,
        'recent_completed': recent_completed,
        'in_progress': in_progress,
    }
    return render(request, 'profile.html', context)


@login_required
def profile_edit_view(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('profile')
    
    return render(request, 'profile_edit.html', {'user': request.user})


@login_required
def change_password_view(request):
    """Смена пароля"""
    if request.method == 'POST':
        user = request.user
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not user.check_password(old_password):
            messages.error(request, 'Текущий пароль неверен')
            return redirect('change_password')
        
        if new_password1 != new_password2:
            messages.error(request, 'Новые пароли не совпадают')
            return redirect('change_password')
        
        if len(new_password1) < 8:
            messages.error(request, 'Пароль должен быть не менее 8 символов')
            return redirect('change_password')
        
        user.set_password(new_password1)
        user.save()
        login(request, user)
        messages.success(request, 'Пароль успешно изменен!')
        return redirect('profile')
    
    return render(request, 'change_password.html')


# =============================================
# 🎮 УРОВНИ
# =============================================

def level_detail(request, level_id):
    """Детальная страница уровня"""
    level = get_object_or_404(SpiritualLevel, id=level_id)
    
    user_progress = None
    if request.user.is_authenticated:
        user_progress = UserProgress.objects.filter(user=request.user, level=level).first()
    
    return render(request, 'level_detail.html', {
        'level': level,
        'user_progress': user_progress
    })


@login_required
def complete_level(request, level_id):
    """Завершение уровня"""
    if request.method == 'POST':
        level = get_object_or_404(SpiritualLevel, id=level_id)
        
        user_progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            level=level
        )
        user_progress.is_completed = True
        user_progress.completed_at = timezone.now()
        user_progress.progress_percentage = 100
        user_progress.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Уровень "{level.title}" пройден!',
            'xp_earned': level.order * 15
        })
    
    return JsonResponse({'success': False, 'error': 'Только POST запросы'}, status=400)


# =============================================
# 📢 ОБЪЯВЛЕНИЯ
# =============================================

def dismiss_announcement(request):
    """Закрытие объявления"""
    if request.method == 'POST':
        announcement_id = request.POST.get('announcement_id')
        dismissed = request.session.get('dismissed_announcements', [])
        if announcement_id not in dismissed:
            dismissed.append(announcement_id)
        request.session['dismissed_announcements'] = dismissed
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)