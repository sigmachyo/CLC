import logging
from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse
from .otp_service import generate_otp_for_user, send_otp_email

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Кастомный адаптер Allauth для KCLC.
    Заменяет стандартные ссылки подтверждения email на 6-значные разовые коды (OTP).
    """

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Генерирует и отправляет 6-значный разовый код вместо длинной ссылки.
        """
        user = emailconfirmation.email_address.user
        email = emailconfirmation.email_address.email

        otp = generate_otp_for_user(user, email=email)
        send_otp_email(otp, request=request)

        if request:
            request.session['otp_user_id'] = user.id
            request.session['otp_email'] = email

    def respond_email_verification_sent(self, request, user):
        """
        После отправки кода сразу перенаправляет пользователя на форму ввода 6 цифр.
        """
        if request:
            request.session['otp_user_id'] = user.id
            request.session['otp_email'] = user.email
        return redirect(reverse('verify_otp'))
