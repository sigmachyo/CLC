from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import re
import logging

# Настройка логгера
logger = logging.getLogger(__name__)

# --- Константы для безопасности ---
# Список самых распространенных паролей (срез из 200 самых популярных)
COMMON_PASSWORDS = {
    "123456", "password", "12345678", "qwerty", "123456789", "12345", "1234",
    "111111", "1234567", "dragon", "123123", "baseball", "abc123", "football",
    "monkey", "letmein", "shadow", "master", "666666", "qwertyuiop", "123321",
    "mustang", "1234567890", "michael", "654321", "superman", "1qaz2wsx",
    "7777777", "121212", "000000", "qazwsx", "123qwe", "killer", "trustno1",
    "jordan", "jennifer", "zxcvbnm", "asdfgh", "hunter", "buster", "soccer",
    "batman", "newyork", "eagle", "thunder", "jesus", "nintendo", "marlboro",
    "access", "hello", "freedom", "whatever", "fuckyou", "lakers", "justice",
    "princess", "mickey", "money", "pepper", "hotdog", "secret", "summer",
    "william", "welcome", "charlie", "qwerty123", "1q2w3e4r", "google",
    "thomas", "admin", "1234qwer", "11111111", "555555", "lovely", "password1"
}

# Временные / одноразовые email-сервисы
TEMPORARY_EMAIL_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com", "10minutemail.com",
    "throwawaymail.com", "trashmail.com", "dispostable.com", "spamgourmet.com",
    "guerrillamail.info", "guerrillamail.biz", "guerrillamail.net",
    "maildrop.cc", "mailnator.com", "tempemail.net", "fakeinbox.com",
    "temp-mail.org", "yopmail.com", "getnada.com", "inboxkitten.com",
    "mail.tm", "spambox.us", "mailinator.net", "tempinbox.com", "spamspot.com"
}

# Лимит регистраций с одного IP за 24 часа
REGISTRATION_IP_LIMIT = 5
REGISTRATION_TIME_WINDOW_HOURS = 24

# --- Вспомогательные функции валидации ---

def validate_username_security(username: str) -> None:
    """Проверяет имя пользователя на подозрительные паттерны."""
    # Блокируем имена, состоящие только из цифр
    if username.isdigit():
        raise ValidationError("Имя пользователя не может состоять только из цифр.")

    # Блокируем имена с большим количеством цифр подряд (бота-паттерн)
    if re.search(r'\d{4,}', username):
        raise ValidationError("Имя пользователя содержит слишком много цифр подряд.")

    # Блокируем имена, состоящие из повторяющихся символов
    if re.fullmatch(r'(.)\1{4,}', username):
        raise ValidationError("Имя пользователя не может состоять из повторяющихся символов.")

    # Проверка на длину и допустимые символы (можно расширить при необходимости)
    if len(username) < 3:
        raise ValidationError("Имя пользователя должно содержать минимум 3 символа.")
    if len(username) > 150:
        raise ValidationError("Имя пользователя слишком длинное (максимум 150 символов).")


def validate_email_security(email: str) -> None:
    """Проверяет email на использование временного/одноразового домена и подозрительные паттерны."""
    domain = email.split('@')[-1].lower()
    if domain in TEMPORARY_EMAIL_DOMAINS:
        raise ValidationError("Использование временных или одноразовых email-адресов запрещено.")

    # Блокируем email, выглядящие как сгенерированные ботами (много цифр подряд)
    if re.search(r'\d{5,}', email.split('@')[0]):
        raise ValidationError("Адрес электронной почты выглядит подозрительно.")


def validate_password_security(password: str, username: str = None, email: str = None) -> None:
    """Проверяет пароль на соответствие строгим требованиям безопасности."""
    if len(password) < 8:
        raise ValidationError('Пароль должен содержать минимум 8 символов.')

    if password.lower() in COMMON_PASSWORDS:
        raise ValidationError('Пароль слишком простой и часто используется.')

    # Проверка на наличие различных типов символов
    if not re.search(r'[A-ZА-Я]', password):
        raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву.')
    if not re.search(r'[a-zа-я]', password):
        raise ValidationError('Пароль должен содержать хотя бы одну строчную букву.')
    if not re.search(r'[0-9]', password):
        raise ValidationError('Пароль должен содержать хотя бы одну цифру.')
    if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:,.<>?/\\|`~]', password):
        raise ValidationError('Пароль должен содержать хотя бы один спецсимвол (!@#$% и т.д.).')

    # Не должен содержать имя пользователя
    if username and username in password:
        raise ValidationError('Пароль не должен содержать ваше имя пользователя.')

    # Не должен содержать часть имени пользователя (например, "user" из "user123")
    if username and len(username) > 3 and username[:-3] in password:
        raise ValidationError('Пароль не должен содержать часть вашего имени пользователя.')

    # Не должен содержать часть email (например, "mail" из "mail@domain.com")
    if email and len(email) > 5:
        local_part = email.split('@')[0]
        if len(local_part) > 4 and local_part in password:
            raise ValidationError('Пароль не должен содержать часть вашего email.')

def check_ip_registration_limit(ip_address: str) -> None:
    """
    Проверяет, не превышен ли лимит регистраций с данного IP-адреса за последние 24 часа.
    """
    if not ip_address:
        logger.warning("Не удалось получить IP-адрес для проверки лимита.")
        return

    time_threshold = timezone.now() - timedelta(hours=REGISTRATION_TIME_WINDOW_HOURS)
    recent_registrations = User.objects.filter(
        date_joined__gte=time_threshold,
        # Мы храним IP при регистрации? Если нет, то эта проверка не сработает.
        # Рекомендуется добавить поле last_ip в модель User или создать отдельную
        # модель RegistrationAttempt для точного отслеживания.
        # Пока оставляем заглушку.
        # Пример:
        # last_ip=ip_address
    ).count()

    if recent_registrations >= REGISTRATION_IP_LIMIT:
        logger.warning(f"Превышен лимит регистраций с IP {ip_address}. Попыток: {recent_registrations}")
        raise ValidationError("С вашего IP-адреса было выполнено слишком много попыток регистрации за последние 24 часа. Пожалуйста, попробуйте позже.")

# --- Формы ---

class RegisterForm(forms.Form):
    """Улучшенная форма регистрации с расширенной валидацией."""
    username = forms.CharField(
        max_length=150,
        min_length=3,
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'placeholder': 'Логин (мин 3 символа)',
            'autocomplete': 'username',
            'autofocus': True,
        }),
        error_messages={
            'min_length': 'Имя пользователя должно содержать минимум 3 символа.',
            'max_length': 'Имя пользователя слишком длинное (максимум 150 символов).',
        }
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email',
            'autocomplete': 'email',
        }),
        error_messages={
            'invalid': 'Пожалуйста, введите корректный email-адрес.',
        }
    )
    password1 = forms.CharField(
        min_length=8,
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Пароль (мин 8 символов)',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        min_length=8,
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Повторите пароль',
            'autocomplete': 'new-password',
        }),
    )

    def __init__(self, *args, **kwargs):
        # Принимаем request для получения IP-адреса
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()

        # Запускаем все проверки для имени пользователя
        try:
            validate_username_security(username)
        except ValidationError as e:
            raise ValidationError(e.message)

        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Имя пользователя уже занято. Пожалуйста, выберите другое.')

        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        # Запускаем проверки email
        try:
            validate_email_security(email)
        except ValidationError as e:
            raise ValidationError(e.message)

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Этот email уже используется. Если вы забыли пароль, воспользуйтесь функцией восстановления.')

        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        username = self.cleaned_data.get('username', '')
        email = self.cleaned_data.get('email', '')

        # Запускаем комплексную проверку пароля
        try:
            validate_password_security(password, username, email)
        except ValidationError as e:
            raise ValidationError(e.message)

        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')

        if p1 and p2 and p1 != p2:
            raise ValidationError('Введенные пароли не совпадают.')

        # Проверяем, не передан ли CSRF-токен (защита от атак CSRF)
        if self.request and not self.request.POST.get('csrfmiddlewaretoken'):
            logger.warning("Попытка регистрации без CSRF-токена.")
            raise ValidationError('Недействительный запрос. Пожалуйста, обновите страницу и попробуйте снова.')

        # Проверка лимита регистраций с IP (если есть request)
        if self.request and hasattr(self.request, 'META'):
            ip_address = self.request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                         self.request.META.get('REMOTE_ADDR')
            if ip_address:
                try:
                    # Убедитесь, что функция check_ip_registration_limit реализована должным образом,
                    # или закомментируйте вызов, если у вас нет поля last_ip.
                    # check_ip_registration_limit(ip_address)
                    pass  # Временная заглушка до реализации хранения IP
                except ValidationError as e:
                    raise ValidationError(e.message)

        return cleaned_data


class LoginForm(forms.Form):
    """Форма входа с базовой валидацией."""
    username = forms.CharField(
        max_length=150,
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'placeholder': 'Логин',
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Пароль',
            'autocomplete': 'current-password',
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        # Небольшая дополнительная проверка: не ввел ли пользователь email вместо username
        username = cleaned_data.get('username', '')
        if '@' in username and '.' in username:
            # Если ввели email, попробуем найти пользователя по email
            try:
                user = User.objects.get(email__iexact=username)
                cleaned_data['username'] = user.username
            except User.DoesNotExist:
                raise ValidationError('Пользователь с таким email не найден.')
        return cleaned_data


class ProfileEditForm(forms.Form):
    """Форма редактирования профиля."""
    first_name = forms.CharField(
        max_length=150, required=False, label='Имя',
        widget=forms.TextInput(attrs={'placeholder': 'Имя'}),
    )
    last_name = forms.CharField(
        max_length=150, required=False, label='Фамилия',
        widget=forms.TextInput(attrs={'placeholder': 'Фамилия'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Email'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        # Проверка на временный email
        try:
            validate_email_security(email)
        except ValidationError as e:
            raise ValidationError(e.message)
        return email


class ChangePasswordForm(forms.Form):
    """Форма смены пароля с улучшенной валидацией."""
    old_password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Текущий пароль'}),
    )
    new_password1 = forms.CharField(
        min_length=8,
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Новый пароль (мин 8 символов)'}),
    )
    new_password2 = forms.CharField(
        min_length=8,
        label='Повторите новый пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите новый пароль'}),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password', '')
        if self.user and not self.user.check_password(old_password):
            raise ValidationError('Текущий пароль неверен.')
        return old_password

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1', '')
        username = self.user.username if self.user else ''
        email = self.user.email if self.user else ''

        try:
            validate_password_security(password, username, email)
        except ValidationError as e:
            raise ValidationError(e.message)

        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')

        if p1 and p2 and p1 != p2:
            raise ValidationError('Новые пароли не совпадают.')

        return cleaned_data


class PrayerRequestForm(forms.Form):
    """Форма добавления молитвенной нужды с базовой санитацией."""
    title = forms.CharField(
        max_length=200,
        label='Тема',
        widget=forms.TextInput(attrs={'placeholder': 'Тема молитвы'}),
        error_messages={
            'required': 'Пожалуйста, укажите тему молитвы.',
            'max_length': 'Тема не должна превышать 200 символов.',
        }
    )
    description = forms.CharField(
        label='Описание',
        widget=forms.Textarea(attrs={
            'placeholder': 'Опишите вашу нужду...',
            'rows': 4,
        }),
        error_messages={
            'required': 'Пожалуйста, опишите вашу нужду.',
        }
    )
    is_public = forms.BooleanField(
        required=False,
        initial=True,
        label='Показывать публично на молитвенной стене',
    )

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 3:
            raise ValidationError('Тема должна содержать минимум 3 символа.')
        # Простая защита от спама
        if len(title) > 200:
            raise ValidationError('Тема слишком длинная.')
        return title

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if len(description) < 10:
            raise ValidationError('Описание должно содержать минимум 10 символов.')
        if len(description) > 5000:
            raise ValidationError('Описание слишком длинное (максимум 5000 символов).')
        return description