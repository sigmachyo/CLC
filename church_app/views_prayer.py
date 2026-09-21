from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import PrayerRequest, Revelation, RevelationReaction
from .forms import PrayerRequestForm, RevelationForm


def prayer_list(request):
    """
    Список публичных молитвенных нужд с фильтрами по статусу и категориям.
    Соблюдает конфиденциальность и 152-ФЗ.
    """
    tab = request.GET.get('tab', 'all')
    category = request.GET.get('category', 'all')

    qs = PrayerRequest.objects.filter(is_public=True)

    # Статистика
    total_public = qs.count()
    active_count = qs.filter(is_answered=False).count()
    answered_count = qs.filter(is_answered=True).count()

    # Загружаем все публичные молитвы для мгновенного переключения категорий без перезагрузки
    prayers = qs.order_by('-is_answered', '-created_at')

    # Проверяем, какие молитвы уже поддержаны текущим пользователем / сессией
    supported_ids = set()
    if request.user.is_authenticated:
        supported_ids = set(
            PrayerRequest.objects.filter(supporters=request.user).values_list('id', flat=True)
        )
    else:
        for p in prayers:
            if request.session.get(f'prayer_supported_{p.id}'):
                supported_ids.add(p.id)

    context = {
        'prayers': prayers,
        'current_tab': tab,
        'current_category': category,
        'total_public': total_public,
        'active_count': active_count,
        'answered_count': answered_count,
        'categories': PrayerRequest.PRAYER_CATEGORIES,
        'supported_ids': supported_ids,
        'title': 'Молитвенная стена | KCLC',
    }
    return render(request, 'prayer_list.html', context)


@login_required
def prayer_add(request):
    """
    Добавление новой молитвенной нужды.
    Поддерживает анонимную публикацию и конфиденциальный режим (только пасторам).
    """
    if request.method == 'POST':
        form = PrayerRequestForm(request.POST)
        if form.is_valid():
            is_public = form.cleaned_data['is_public']
            is_anonymous = form.cleaned_data['is_anonymous']
            category = form.cleaned_data['category']

            prayer = PrayerRequest.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                category=category,
                is_public=is_public,
                is_anonymous=is_anonymous,
            )

            if is_public:
                messages.success(request, 'Ваша нужда размещена на молитвенной стене церкви.')
                return redirect('prayer_list')
            else:
                messages.success(
                    request,
                    'Ваша конфиденциальная нужда передана пасторам и молитвенной команде церкви. '
                    'Она защищена и не отображается публично.'
                )
                return redirect('my_prayers')
    else:
        form = PrayerRequestForm()

    return render(request, 'prayer_add.html', {
        'title': 'Оставить нужду | KCLC',
        'form': form,
    })


def prayer_support(request, prayer_id):
    """
    Поддержать в молитве («Я молюсь»).
    Поддерживает как AJAX-запросы без перезагрузки, так и стандартную отправку форм.
    """
    prayer = get_object_or_404(PrayerRequest, id=prayer_id, is_public=True)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        supported_key = f'prayer_supported_{prayer_id}'
        already_supported = False

        if request.user.is_authenticated:
            already_supported = prayer.supporters.filter(id=request.user.id).exists()
        else:
            already_supported = bool(request.session.get(supported_key))

        if already_supported:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Вы уже присоединились к этой молитве.',
                    'count': prayer.prayer_count,
                    'already_supported': True
                })
            messages.info(request, 'Вы уже поддержали эту молитву.')
            return redirect('prayer_list')

        # Увеличиваем счётчик и фиксируем поддержку
        prayer.prayer_count += 1
        if request.user.is_authenticated:
            prayer.supporters.add(request.user)
        prayer.save()
        request.session[supported_key] = True

        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': f'Слава Богу! Вы присоединились к молитве: «{prayer.title}»',
                'count': prayer.prayer_count,
                'already_supported': False
            })

        messages.success(request, f'Вы присоединились к молитве за: «{prayer.title}»')

    return redirect('prayer_list')


@login_required
def my_prayers(request):
    """
    Личный молитвенный дневник пользователя:
    - Активные нужды
    - Отвеченные молитвы (свидетельства)
    - Конфиденциальные нужды (только пасторам)
    """
    user_prayers = PrayerRequest.objects.filter(user=request.user)

    active_prayers = user_prayers.filter(is_answered=False).order_by('-created_at')
    answered_prayers = user_prayers.filter(is_answered=True).order_by('-answered_at')
    private_prayers = user_prayers.filter(is_public=False).order_by('-created_at')

    context = {
        'active_prayers': active_prayers,
        'answered_prayers': answered_prayers,
        'private_prayers': private_prayers,
        'title': 'Мои молитвы | KCLC',
    }
    return render(request, 'my_prayers.html', context)


@login_required
def prayer_toggle_answered(request, prayer_id):
    """Отметить как отвеченную / вернуть в активные"""
    prayer = get_object_or_404(PrayerRequest, id=prayer_id, user=request.user)
    if request.method == 'POST':
        prayer.is_answered = not prayer.is_answered
        prayer.answered_at = timezone.now() if prayer.is_answered else None
        prayer.save()
        status = '«Отвечена» (Слава Богу!)' if prayer.is_answered else '«Активна»'
        messages.success(request, f'Статус нужды обновлён на: {status}')
    return redirect('my_prayers')
def revelation_list(request):
    """Список публичных откровений и свидетельств с подсчетом реакций."""
    qs = Revelation.objects.filter(is_public=True).order_by('-created_at')
    
    revelations = []

    for rev in qs:
        # Считаем количество каждой реакции
        reactions = {
            'amen': rev.reactions.filter(reaction_type='amen').count(),
            'glory': rev.reactions.filter(reaction_type='glory').count(),
            'fire': rev.reactions.filter(reaction_type='fire').count(),
            'grace': rev.reactions.filter(reaction_type='grace').count(),
        }
        user_reaction = None
        if request.user.is_authenticated:
            user_react = rev.reactions.filter(user=request.user).first()
            if user_react:
                user_reaction = user_react.reaction_type

        revelations.append({
            'revelation': rev,
            'reactions': reactions,
            'user_reaction': user_reaction
        })

    context = {
        'revelations_data': revelations,
        'title': 'Откровения и свидетельства | KCLC'
    }
    return render(request, 'revelation_list.html', context)


@login_required
def revelation_add(request):
    """Добавление нового откровения."""
    if request.method == 'POST':
        form = RevelationForm(request.POST)
        if form.is_valid():
            is_public = form.cleaned_data['is_public']
            is_anonymous = form.cleaned_data['is_anonymous']
            
            Revelation.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                is_public=is_public,
                is_anonymous=is_anonymous,
            )

            messages.success(request, 'Слава Богу! Ваше свидетельство опубликовано.')
            return redirect('revelation_list')
    else:
        form = RevelationForm()

    return render(request, 'revelation_add.html', {
        'title': 'Поделиться откровением | KCLC',
        'form': form,
    })


@login_required
def revelation_react(request, pk):
    """AJAX-реакции (Toggle: добавить/убрать)"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        revelation = get_object_or_404(Revelation, pk=pk, is_public=True)
        reaction_type = request.POST.get('reaction_type')
        
        valid_types = dict(RevelationReaction.REACTION_CHOICES).keys()
        if reaction_type not in valid_types:
            return JsonResponse({'success': False, 'error': 'Invalid reaction type'}, status=400)
            
        # У пользователя может быть только одна реакция на пост
        existing_reaction = RevelationReaction.objects.filter(revelation=revelation, user=request.user).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # Если нажал на ту же - удаляем
                existing_reaction.delete()
                action = 'removed'
            else:
                # Меняем реакцию
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                action = 'updated'
        else:
            RevelationReaction.objects.create(revelation=revelation, user=request.user, reaction_type=reaction_type)
            action = 'added'
            
        # Пересчитываем
        counts = {
            'amen': revelation.reactions.filter(reaction_type='amen').count(),
            'glory': revelation.reactions.filter(reaction_type='glory').count(),
            'fire': revelation.reactions.filter(reaction_type='fire').count(),
            'grace': revelation.reactions.filter(reaction_type='grace').count(),
        }
        
        return JsonResponse({
            'success': True,
            'action': action,
            'counts': counts,
            'current_reaction': reaction_type if action != 'removed' else None
        })
    return JsonResponse({'success': False}, status=400)
