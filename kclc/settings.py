import os
import ipaddress
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY is not set in environment variables")

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

_allowed_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,*')
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(',') if host.strip()]
ALLOWED_HOSTS.extend(['*'])

# Web Push — ключи из .env
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_ADMIN_EMAIL = os.environ.get('VAPID_ADMIN_EMAIL', 'mailto:webmaster@localhost')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.vk',
    'allauth.socialaccount.providers.yandex',

    # captcha
    'hcaptcha',

    'church_app',  # Ваше приложение
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Add the account middleware:
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'kclc.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Указываем папку с шаблонами
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kclc.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Krasnoyarsk'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Для разработки
STATIC_ROOT = BASE_DIR / 'staticfiles'    # Для продакшена

# Media files (загружаемые пользователями)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'  # URL для входа (allauth)
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# -------------------------------------------------------
# Кастомные страницы ошибок
# -------------------------------------------------------
handler404 = 'church_app.views.custom_404'
handler500 = 'church_app.views.custom_500'

# -------------------------------------------------------
# Безопасность
# -------------------------------------------------------
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

# CSRF trusted origins (добавь свой домен в .env и здесь в production)
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1',
    'http://localhost',
]
_extra_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if _extra_origins:
    CSRF_TRUSTED_ORIGINS += [o.strip() for o in _extra_origins.split(',') if o.strip()]

# CSP отключён — подключается позже после стабилизации через django-csp
# (при необходимости раскомментировать и добавить 'csp.middleware.CSPMiddleware' в MIDDLEWARE)

# -------------------------------------------------------
# Session
# -------------------------------------------------------
SESSION_COOKIE_AGE = 31536000  # 365 days
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# -------------------------------------------------------------
# JAZZMIN ADMIN CONFIGURATION (Midnight Gold Theme)
# -------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "CLC Panel",
    "site_header": "CLC Admin",
    "site_brand": "CLC Красноярск",
    "site_icon": "fas fa-church",
    "site_logo_classes": "img-circle",
    "welcome_sign": "Добро пожаловать в панель CLC",
    "copyright": "CLC Krasnoyarsk",
    "search_model": ["auth.User", "church_app.Event"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "На сайт", "url": "/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "church_app.Video": "fas fa-video",
        "church_app.Announcement": "fas fa-bullhorn",
        "church_app.SpiritualLevel": "fas fa-route",
        "church_app.DailyVerse": "fas fa-book-open",
        "church_app.Event": "fas fa-calendar-check",
        "church_app.EventRegistration": "fas fa-ticket-alt",
        "church_app.PrayerRequest": "fas fa-pray",
        "church_app.KidsContent": "fas fa-child",
        "church_app.KidsProgress": "fas fa-star",
        "church_app.ChatRoom": "fas fa-comments",
        "church_app.ChatMessage": "fas fa-comment-dots",
        "church_app.Category": "fas fa-tags",
        "church_app.BiblePlan": "fas fa-book",
        "church_app.BibleReading": "fas fa-bookmark",
        "church_app.UserProgress": "fas fa-chart-line",
        "church_app.UserBibleProgress": "fas fa-tasks",
        "church_app.PushSubscription": "fas fa-bell",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
    "order_with_respect_to": ["church_app", "church_app.DailyVerse", "church_app.Event", "church_app.Announcement", "church_app.Video", "church_app.PrayerRequest"],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-navy",
    "accent": "accent-warning",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-navy",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# ---------------------------------------------------------
# DJANGO-ALLAUTH SETTINGS (v65+)
# ---------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
SITE_ID = 1

# ── Поля при регистрации (новый синтаксис v65+)
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# ── Методы входа: по email ИЛИ по нику
ACCOUNT_LOGIN_METHODS = {'username', 'email'}

# ── Email — обязателен, уникален
ACCOUNT_UNIQUE_EMAIL = True

# ── Кастомный адаптер Allauth (отправка 6-значных OTP кодов)
ACCOUNT_ADAPTER = 'church_app.adapter.CustomAccountAdapter'

# ── Верификация email обязательна через OTP-код
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = True

# ── Кастомный валидатор email (отсеивает одноразовые домены)
ACCOUNT_EMAIL_VALIDATORS = [
    'church_app.validators.BlockDisposableEmailValidator',
]

# ── Политика паролей
ACCOUNT_PASSWORD_MIN_LENGTH = 8

# ── Email backend (Настройка под bot.kclc@mail.ru)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.mail.ru')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '465'))
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'True').lower() in ('true', '1')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False').lower() in ('true', '1')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'bot.kclc@mail.ru')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'KCLC <bot.kclc@mail.ru>')

# Если пароль указан в .env — шлём через реальный SMTP mail.ru. Иначе выводим в консоль терминала
if EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# ---------------------------------------------------------
# OAuth — ключи из переменных окружения (.env файл)
# Только VK и Яндекс (Google удален по запросу)
# ---------------------------------------------------------
SOCIALACCOUNT_PROVIDERS = {
    'vk': {
        'APP': {
            'client_id': os.environ.get('VK_CLIENT_ID', 'change-me'),
            'secret': os.environ.get('VK_CLIENT_SECRET', 'change-me'),
            'key': '',
        },
    },
    'yandex': {
        'APP': {
            'client_id': os.environ.get('YANDEX_CLIENT_ID', 'change-me'),
            'secret': os.environ.get('YANDEX_CLIENT_SECRET', 'change-me'),
            'key': '',
        },
    },
}

# При OAuth-регистрации — не требовать повторного ввода email/никнейма
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# ---------------------------------------------------------
# hCaptcha — защита форм регистрации и сброса пароля
# Получить ключи бесплатно на https://www.hcaptcha.com/
# Для тестирования используем тестовые ключи hCaptcha (всегда проходят)
# ---------------------------------------------------------
HCAPTCHA_SITEKEY = os.environ.get('HCAPTCHA_SITEKEY', '10000000-ffff-ffff-ffff-000000000001')
HCAPTCHA_SECRET = os.environ.get('HCAPTCHA_SECRET', '0x0000000000000000000000000000000000000000')
