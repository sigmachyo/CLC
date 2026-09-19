import json
import logging
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from allauth.account.models import EmailAddress

from .otp_service import (
    generate_otp_for_user,
    send_otp_email,
    verify_otp_code,
    can_resend_otp,
    RESEND_COOLDOWN_SECONDS
)
from .forms import (
    validate_username_security,
    validate_email_security,
    TEMPORARY_EMAIL_DOMAINS
)

logger = logging.getLogger(__name__)


def _get_otp_target_user(request):
    """Возвращает пользователя, ожидающего подтверждения OTP."""
    user_id = request.session.get('otp_user_id')
    if user_id:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            pass

    if request.user.is_authenticated:
        return request.user

    return None


def verify_otp_view(request):
    """
    Страница ввода 6-значного одноразового кода подтверждения email.
    """
    target_user = _get_otp_target_user(request)

    if not target_user:
        messages.info(request, "Сессия подтверждения истекла. Пожалуйста, войдите в аккаунт.")
        return redirect('account_login')

    # Проверяем, может email уже подтверждён
    email = target_user.email
    is_verified = EmailAddress.objects.filter(user=target_user, email__iexact=email, verified=True).exists()
    if is_verified and target_user.is_active:
        messages.success(request, "Ваш email уже подтверждён.")
        return redirect('profile')

    error_message = None

    if request.method == 'POST':
        # Поддерживаем как склеенный 'code', так и 6 раздельных инпутов code_1..code_6
        raw_code = request.POST.get('code', '').strip()
        if not raw_code:
            parts = [request.POST.get(f'code_{i}', '').strip() for i in range(1, 7)]
            raw_code = ''.join(parts)

        success, msg = verify_otp_code(target_user, raw_code)
        if success:
            # Логиним пользователя
            target_user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')

            # Очищаем сессию
            request.session.pop('otp_user_id', None)
            request.session.pop('otp_email', None)

            messages.success(request, "🎉 Поздравляем! Ваш email успешно подтверждён. Добро пожаловать в KCLC!")
            return redirect('profile')
        else:
            error_message = msg

    can_resend, seconds_left = can_resend_otp(target_user)

    context = {
        'target_user': target_user,
        'email': email,
        'error_message': error_message,
        'can_resend': can_resend,
        'seconds_left': seconds_left,
        'cooldown_total': RESEND_COOLDOWN_SECONDS,
    }
    return render(request, 'account/otp_verify.html', context)


@require_http_methods(['POST', 'GET'])
def resend_otp_view(request):
    """
    Повторная отправка 6-значного кода с проверкой кулдауна.
    """
    target_user = _get_otp_target_user(request)
    if not target_user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Сессия не найдена. Войдите заново.'}, status=400)
        messages.error(request, "Сессия не найдена. Пожалуйста, войдите в аккаунт.")
        return redirect('account_login')

    can_resend, seconds_left = can_resend_otp(target_user)
    if not can_resend:
        msg = f"Пожалуйста, подождите {seconds_left} сек. перед повторной отправкой кода."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg, 'seconds_left': seconds_left}, status=429)
        messages.warning(request, msg)
        return redirect('verify_otp')

    try:
        otp = generate_otp_for_user(target_user)
        send_otp_email(otp, request=request)
        msg = f"Новый проверочный код успешно отправлен на {target_user.email}"
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg, 'cooldown': RESEND_COOLDOWN_SECONDS})
        messages.success(request, msg)
    except Exception as e:
        logger.error(f"Ошибка повторной генерации OTP: {e}")
        msg = "Не удалось отправить код. Пожалуйста, попробуйте чуть позже."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=500)
        messages.error(request, msg)

    return redirect('verify_otp')


def check_username_api(request):
    """
    Live AJAX API для проверки занятости и корректности никнейма.
    Вызывается прямо во время ввода в форме регистрации.
    """
    username = request.GET.get('username', '').strip()

    if not username:
        return JsonResponse({'valid': False, 'available': False, 'message': 'Введите никнейм.'})

    if len(username) < 3:
        return JsonResponse({'valid': False, 'available': False, 'message': 'Минимум 3 символа.'})

    if len(username) > 150:
        return JsonResponse({'valid': False, 'available': False, 'message': 'Слишком длинный (макс 150).'})

    # Проверка на буквы/цифры/_/-
    import re
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return JsonResponse({
            'valid': False,
            'available': False,
            'message': 'Допустимы только латинские буквы, цифры, дефис, точка и _'
        })

    # Проверка на чисто цифры
    if username.isdigit():
        return JsonResponse({'valid': False, 'available': False, 'message': 'Не может состоять только из цифр.'})

    # Проверка занятости (регистронезависимо)
    exists = User.objects.filter(username__iexact=username).exists()
    if exists:
        return JsonResponse({'valid': True, 'available': False, 'message': 'Этот никнейм уже занят.'})

    return JsonResponse({'valid': True, 'available': True, 'message': 'Никнейм свободен!'})


def check_email_api(request):
    """
    Live AJAX API для проверки формата email и блокировки одноразовых почт.
    """
    email = request.GET.get('email', '').strip().lower()

    if not email:
        return JsonResponse({'valid': False, 'available': False, 'message': 'Введите email.'})

    import re
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return JsonResponse({'valid': False, 'available': False, 'message': 'Некорректный формат email.'})

    domain = email.split('@')[-1].lower()
    if domain in TEMPORARY_EMAIL_DOMAINS:
        return JsonResponse({
            'valid': False,
            'available': False,
            'disposable': True,
            'message': 'Одноразовые почтовые ящики запрещены.'
        })

    # Проверка уникальности
    exists = User.objects.filter(email__iexact=email).exists()
    if exists:
        return JsonResponse({
            'valid': True,
            'available': False,
            'message': 'Аккаунт с таким email уже существует. Войдите через форму входа.'
        })

    return JsonResponse({'valid': True, 'available': True, 'message': 'Email свободен и корректен!'})

