from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PrayerRequest
from .forms import PrayerRequestForm
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
        form = PrayerRequestForm(request.POST)
        if form.is_valid():
            PrayerRequest.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                is_public=form.cleaned_data['is_public'],
            )
            messages.success(request, 'Ваша нужда добавлена на молитвенную стену.')
            return redirect('prayer_list')
    else:
        form = PrayerRequestForm()
    return render(request, 'prayer_add.html', {'title': 'Добавить нужду', 'form': form})

@login_required
def prayer_support(request, prayer_id):
    """Поддержать в молитве (+1) — с защитой от повторного голосования"""
    prayer = get_object_or_404(PrayerRequest, id=prayer_id)
    if request.method == 'POST':
        supported_key = f'prayer_supported_{prayer_id}'
        if request.session.get(supported_key):
            messages.info(request, 'Вы уже поддержали эту молитву.')
        else:
            prayer.prayer_count += 1
            prayer.save()
            request.session[supported_key] = True
            messages.success(request, f'Вы присоединились к молитве за: {prayer.title}')
    return redirect('prayer_list')

@login_required
def my_prayers(request):
    """
    Личные нужды пользователя — разделены на активные и отвеченные.
    Использует кастомный менеджер PrayerRequest.objects.active() и .answered()
    """
    user_prayers = PrayerRequest.objects.filter(user=request.user)
    
    context = {
        'active_prayers': user_prayers.filter(is_answered=False).order_by('-created_at'),
        'answered_prayers': user_prayers.filter(is_answered=True).order_by('-answered_at'),
        'title': 'Мои молитвы'
    }
    return render(request, 'my_prayers.html', context)

@login_required
def prayer_toggle_answered(request, prayer_id):
    """Отметить как отвеченную / снять отметку"""
    prayer = get_object_or_404(PrayerRequest, id=prayer_id, user=request.user)
    if request.method == 'POST':
        prayer.is_answered = not prayer.is_answered
        prayer.answered_at = timezone.now() if prayer.is_answered else None
        prayer.save()
        status = 'отвечена' if prayer.is_answered else 'активна'
        messages.success(request, f'Нужда отмечена как {status}.')
    return redirect('my_prayers')