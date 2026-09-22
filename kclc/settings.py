import os
import ipaddress
from pathlib import Path
try:
    import dj_database_url
except ImportError:
    dj_database_url = None

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

if not DEBUG and SECRET_KEY.startswith('django-insecure-'):
    import warnings
    warnings.warn("DJANGO_SECRET_KEY is using a default insecure key. Please set a random secret key in production!", RuntimeWarning)

_allowed_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if _allowed_hosts:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(',') if host.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0', '*']
else:
    ALLOWED_HOSTS = [
        '127.0.0.1', 'localhost', '0.0.0.0',
        'new.kclc.ru', 'kclc.ru', 'www.new.kclc.ru', 'www.kclc.ru',
        'newkclc.ru', 'www.newkclc.ru',
        'new.kclc.tw1.ru', 'cr89358.tw1.ru', 'vh458.timeweb.ru',
    ]

# Web Push — ключи из .env (с надежными дефолтами)
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', 'BPWzM8Sg21koEirpUOKjfqqqUeOL6c4PrF3KwT32QYT9pQP6R1Da9u8jSS0UMTkx4DL_75iOadzTAPNSOJVGlpo')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', 'a4IVr9jA_SyFG-cohYOfztaM0Ul3xrXZI8qgl6a_KKk')
VAPID_ADMIN_EMAIL = os.environ.get('VAPID_ADMIN_EMAIL', 'mailto:bot.kclc@mail.ru')

INSTALLED_APPS = []

# Admin theme: unfold if available, otherwise jazzmin
try:
    import unfold
    INSTALLED_APPS.extend([
        'unfold',
        'unfold.contrib.filters',
        'unfold.contrib.forms',
        'unfold.contrib.inlines',
    ])
except ImportError:
    try:
        import jazzmin
        INSTALLED_APPS.append('jazzmin')
    except ImportError:
        pass

INSTALLED_APPS.extend([
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
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
])

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

# Database: поддержка Timeweb MySQL, PostgreSQL (DATABASE_URL) и откат на SQLite
if os.environ.get('DB_ENGINE') or (os.environ.get('DB_NAME') and not os.environ.get('DATABASE_URL')):
    DATABASES = {
        'default': {
            'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.mysql'),
            'NAME': os.environ.get('DB_NAME', 'cr89358_new'),
            'USER': os.environ.get('DB_USER', 'cr89358_new'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'ChurchPass2026'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
            },
        }
    }
elif 'DATABASE_URL' in os.environ and dj_database_url:
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    _default_db_url = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    if dj_database_url:
        DATABASES = {
            'default': dj_database_url.config(
                default=_default_db_url,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
    else:
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

# Static files (CSS, JavaScript, Images) — раздача через WhiteNoise сжатие и кеш
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_MAX_AGE = 31536000

# Media files (загружаемые пользователями)
MEDIA_URL = '/media/'
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
# Безопасность и SSL
# -------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT or os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT or os.environ.get('CSRF_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')

if SECURE_SSL_REDIRECT:
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

# ── Referrer-Policy HTTP Header (YouTube Embedded Player API Requirement)
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CSRF trusted origins (добавь свой домен в .env или переменные окружения)
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1',
    'http://localhost',
    'https://127.0.0.1',
    'https://localhost',
]
_extra_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if _extra_origins:
    for origin in _extra_origins.split(','):
        origin = origin.strip()
        if origin:
            if not origin.startswith(('http://', 'https://')):
                CSRF_TRUSTED_ORIGINS.extend([f'https://{origin}', f'http://{origin}'])
            else:
                CSRF_TRUSTED_ORIGINS.append(origin)

for host in ALLOWED_HOSTS:
    if host and host not in ('*', '127.0.0.1', 'localhost', '0.0.0.0'):
        CSRF_TRUSTED_ORIGINS.extend([f'https://{host}', f'http://{host}'])
# Удаляем дубликаты
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))

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
SOCIALACCOUNT_ADAPTER = 'church_app.adapter.CustomSocialAccountAdapter'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'

SOCIALACCOUNT_PROVIDERS = {
    'vk': {
        'APP': {
            'client_id': os.environ.get('VK_CLIENT_ID', '').strip(),
            'secret': os.environ.get('VK_CLIENT_SECRET', '').strip(),
            'key': '',
        },
        'SCOPE': ['email', 'photos'],
        'FIELDS': ['first_name', 'last_name', 'screen_name', 'sex', 'bdate', 'photo_200', 'photo_max_orig'],
    },
    'yandex': {
        'APP': {
            'client_id': os.environ.get('YANDEX_CLIENT_ID', '').strip(),
            'secret': os.environ.get('YANDEX_CLIENT_SECRET', '').strip(),
            'key': '',
        },
        'SCOPE': ['login:email', 'login:info', 'login:avatar'],
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

# ---------------------------------------------------------
# Production Logging (Console / Docker / Gunicorn friendly)
# ---------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING' if not DEBUG else 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'church_app': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


