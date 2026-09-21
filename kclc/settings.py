import os
import ipaddress
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Загрузка переменных из .env (с поддержкой dotenv или ручного парсера)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

env_file = BASE_DIR / '.env'
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key not in os.environ:
                    os.environ[key] = val

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-local-dev-key-do-not-use-in-prod')

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

_allowed_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,*')
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(',') if host.strip()]
ALLOWED_HOSTS.extend(['*'])

# Web Push — ключи из .env (с надежными дефолтами)
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', 'BPWzM8Sg21koEirpUOKjfqqqUeOL6c4PrF3KwT32QYT9pQP6R1Da9u8jSS0UMTkx4DL_75iOadzTAPNSOJVGlpo')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', 'a4IVr9jA_SyFG-cohYOfztaM0Ul3xrXZI8qgl6a_KKk')
VAPID_ADMIN_EMAIL = os.environ.get('VAPID_ADMIN_EMAIL', 'mailto:bot.kclc@mail.ru')

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.inlines',
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
    'django.middleware.gzip.GZipMiddleware',
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
                'church_app.context_processors.oauth_providers_status',
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
SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_PROVIDERS = {
    'vk': {
        'APP': {
            'client_id': os.environ.get('VK_CLIENT_ID', ''),
            'secret': os.environ.get('VK_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['email'],
    },
    'yandex': {
        'APP': {
            'client_id': os.environ.get('YANDEX_CLIENT_ID', ''),
            'secret': os.environ.get('YANDEX_CLIENT_SECRET', ''),
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

# Fast in-memory caching to prevent server blocking/freezing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'kclc-cache',
        'TIMEOUT': 300,
    }
}

# ── Referrer-Policy HTTP Header (YouTube Embedded Player API Requirement)
# Sends "Referrer-Policy: strict-origin-when-cross-origin" on all HTTP responses
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

