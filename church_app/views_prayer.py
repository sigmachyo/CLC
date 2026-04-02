from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PrayerRequest
from django.utils import timezone

def prayer_list(request):
    """Список публичных молитвенных нужд"""
    prayers = PrayerRequest.objects.filter(is_public=True).order_by('-created_at')
    
    context = {
        'prayers': prayers,
        'title': 'Молитвенная стена'
    }
    return render(request, 'prayer_list.html', context)

@login_required
def prayer_add(request):
    """Добавление новой молитвенной нужды"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        is_public = request.POST.get('is_public') == 'on'
        
        if title and description:
            PrayerRequest.objects.create(
                user=request.user,
                title=title,
                description=description,
                is_public=is_public
            )
            messages.success(request, 'Ваша нужда добавлена на молитвенную стену.')
            return redirect('prayer_list')
            
    return render(request, 'prayer_add.html', {'title': 'Добавить нужду'})

@login_required
def prayer_support(request, prayer_id):
    """Поддержать в молитве (+1)"""
    prayer = get_object_or_404(PrayerRequest, id=prayer_id)
    if request.method == 'POST':
        prayer.prayer_count += 1
        prayer.save()
        messages.success(request, f'Вы присоединились к молитве за: {prayer.title}')
    return redirect('prayer_list')

@login_required
def my_prayers(request):
    """Личные нужды пользователя"""
    prayers = PrayerRequest.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'prayers': prayers,
        'title': 'Мои молитвы'
    }
    return render(request, 'my_prayers.html', context)

@login_required
def prayer_toggle_answered(request, prayer_id):
    """Отметить как отвеченную"""
    prayer = get_object_or_404(PrayerRequest, id=prayer_id, user=request.user)
    if request.method == 'POST':
        prayer.is_answered = not prayer.is_answered
        prayer.answered_at = timezone.now() if prayer.is_answered else None
        prayer.save()
        status = 'отвечена' if prayer.is_answered else 'активна'
        messages.success(request, f'Нужда отмечена как {status}.')
    return redirect('my_prayers')
