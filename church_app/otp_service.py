import secrets
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from allauth.account.models import EmailAddress
from .models import EmailVerificationOTP

logger = logging.getLogger(__name__)

OTP_VALIDITY_MINUTES = 15
OTP_MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60


def generate_otp_for_user(user, email=None):
    """
    Генерирует 6-значный криптографически стойкий OTP-код для пользователя.
    Деактивирует старые неиспользованные коды.
    """
    target_email = (email or user.email or '').strip().lower()
    if not target_email:
        raise ValueError("Пользователь не имеет email адреса.")

    # Инвалидируем предыдущие активные коды
    EmailVerificationOTP.objects.filter(
        user=user,
        email__iexact=target_email,
        is_used=False
    ).update(is_used=True)

    # 6-значный код от 100000 до 999999
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)

    otp = EmailVerificationOTP.objects.create(
        user=user,
        email=target_email,
        code=code,
        expires_at=expires_at,
        is_used=False,
        attempts=0
    )
    return otp


def can_resend_otp(user, email=None):
    """
    Проверяет, прошло ли достаточно времени (cooldown) с момента последней отправки.
    Возвращает (can_resend: bool, seconds_left: int).
    """
    target_email = (email or user.email or '').strip().lower()
    last_otp = EmailVerificationOTP.objects.filter(
        user=user,
        email__iexact=target_email
    ).order_by('-created_at').first()

    if not last_otp:
        return True, 0

    elapsed = (timezone.now() - last_otp.created_at).total_seconds()
    if elapsed < RESEND_COOLDOWN_SECONDS:
        return False, int(RESEND_COOLDOWN_SECONDS - elapsed)

    return True, 0


def send_otp_email(otp, request=None):
    """
    Отправляет 6-значный OTP код на почту пользователя.
    В случае отсутствия или сбоя внешнего SMTP выводит код в консоль, предотвращая 500 ошибку.
    """
    subject = f"Ваш код подтверждения: {otp.code} | KCLC"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'KCLC <bot.kclc@mail.ru>')

    context = {
        'user': otp.user,
        'code': otp.code,
        'expires_minutes': OTP_VALIDITY_MINUTES,
        'email': otp.email,
    }

    try:
        html_message = render_to_string('account/email/otp_message.html', context)
        plain_message = strip_tags(html_message)
    except Exception as e:
        logger.warning(f"Шаблон otp_message.html не найден или вызвал ошибку: {e}")
        plain_message = (
            f"Здравствуйте, {otp.user.username}!\n\n"
            f"Ваш код для подтверждения email на сайте KCLC: {otp.code}\n\n"
            f"Код действителен в течение {OTP_VALIDITY_MINUTES} минут.\n"
            f"Если вы не регистрировались на сайте, просто проигнорируйте это письмо."
        )
        html_message = None

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[otp.email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"OTP code {otp.code} sent to {otp.email}")
        return True
    except Exception as e:
        logger.error(f"Не удалось отправить email через SMTP ({e}). Код OTP для {otp.email}: {otp.code}")
        # Выводим в терминал для локальной разработки
        print("\n" + "=" * 60)
        print(f"📧 [EMAIL OTP ДЛЯ {otp.email}]: {otp.code}")
        print("=" * 60 + "\n")
        return False


def verify_otp_code(user, code):
    """
    Проверяет введенный 6-значный код.
    Если успешен:
      - помечает OTP как использованный
      - помечает EmailAddress в allauth как verified=True
      - активирует пользователя (is_active=True)
    Возвращает (success: bool, message: str).
    """
    clean_code = (code or '').strip()
    if not clean_code or len(clean_code) != 6 or not clean_code.isdigit():
        return False, "Код должен состоять из 6 цифр."

    otp = EmailVerificationOTP.objects.filter(
        user=user,
        is_used=False
    ).order_by('-created_at').first()

    if not otp:
        return False, "Активный код не найден. Запросите отправку кода повторно."

    if timezone.now() > otp.expires_at:
        otp.is_used = True
        otp.save(update_fields=['is_used'])
        return False, "Срок действия кода истёк. Запросите новый код."

    if otp.attempts >= OTP_MAX_ATTEMPTS:
        otp.is_used = True
        otp.save(update_fields=['is_used'])
        return False, "Превышено количество попыток ввода. Запросите новый код."

    if otp.code != clean_code:
        otp.attempts += 1
        otp.save(update_fields=['attempts'])
        remaining = OTP_MAX_ATTEMPTS - otp.attempts
        return False, f"Неверный код. Осталось попыток: {remaining}."

    # Успешная валидация
    otp.is_used = True
    otp.save(update_fields=['is_used'])

    # Активируем пользователя
    user.is_active = True
    user.save(update_fields=['is_active'])

    # Синхронизируем allauth EmailAddress
    email_address, created = EmailAddress.objects.get_or_create(
        user=user,
        email=otp.email,
        defaults={'verified': True, 'primary': True}
    )
    if not created:
        email_address.verified = True
        email_address.primary = True
        email_address.save(update_fields=['verified', 'primary'])

    return True, "Email успешно подтверждён!"

