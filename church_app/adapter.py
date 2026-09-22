import logging
import requests
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from .otp_service import generate_otp_for_user, send_otp_email
from .models import UserProfile

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

    def add_message(self, request, level, message_template=None, message_context=None, extra_tags="", message=None):
        """
        Отключаем системный спам Allauth в сессии ('Вы вышли.', 'Успешный вход под именем...', etc.),
        чтобы они не накапливались и не висели на страницах.
        """
        return


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Кастомный адаптер Allauth для входа через VK ID и Яндекс ID.
    Обеспечивает:
    - 1-клик регистрацию и вход без требования OTP;
    - Автоматическую привязку к существующему аккаунту с тем же email;
    - Корректную обработку профилей без email (генерация уникального fallback email);
    - Автоматический импорт имени, фамилии и аватара в UserProfile.
    """

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        provider = sociallogin.account.provider
        uid = str(sociallogin.account.uid)

        # Если соцсеть не вернула email (часто у VK), формируем уникальный email
        if not user.email:
            user.email = f"{provider}_{uid}@user.kclc.ru"

        # Если никнейм не задан, формируем из данных провайдера
        if not user.username:
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            clean_name = f"{first_name}_{last_name}".strip('_').lower()
            clean_name = "".join(c for c in clean_name if c.isalnum() or c in '_-')
            user.username = f"{clean_name or provider}_{uid[:8]}"[:30]

        return user

    def pre_social_login(self, request, sociallogin):
        """
        Если пользователь с таким email уже зарегистрирован на сайте,
        автоматически привязываем вход через VK/Яндекс к его существующей учетной записи.
        """
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email')
        if not email and sociallogin.user and sociallogin.user.email:
            email = sociallogin.user.email

        if email:
            try:
                existing_user = User.objects.get(email__iexact=email)
                sociallogin.connect(request, existing_user)
            except User.DoesNotExist:
                pass

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        try:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            extra = sociallogin.account.extra_data or {}
            provider = sociallogin.account.provider

            # Синхронизация имени/фамилии если в User они не были заполнены
            first_name = extra.get('first_name')
            last_name = extra.get('last_name')
            changed = False
            if first_name and not user.first_name:
                user.first_name = first_name[:30]
                changed = True
            if last_name and not user.last_name:
                user.last_name = last_name[:30]
                changed = True
            if changed:
                user.save()

            avatar_url = None
            if provider == 'vk':
                avatar_url = extra.get('photo_200') or extra.get('photo_max_orig') or extra.get('photo_100')
                screen_name = extra.get('screen_name')
                if screen_name and not profile.vk:
                    profile.vk = f"https://vk.com/{screen_name}"

            elif provider == 'yandex':
                avatar_id = extra.get('default_avatar_id')
                if avatar_id and not extra.get('is_avatar_empty', False):
                    avatar_url = f"https://avatars.yandex.net/get-yapic/{avatar_id}/islands-200"

            # Скачиваем и сохраняем аватар
            if avatar_url and not profile.avatar:
                try:
                    resp = requests.get(avatar_url, timeout=5)
                    if resp.status_code == 200:
                        filename = f"avatar_{user.id}_{provider}.jpg"
                        profile.avatar.save(filename, ContentFile(resp.content), save=False)
                except Exception as e:
                    logger.warning(f"Could not download avatar for {user.username} from {provider}: {e}")

            profile.save()
        except Exception as e:
            logger.error(f"Error saving profile from social login: {e}")

        return user
