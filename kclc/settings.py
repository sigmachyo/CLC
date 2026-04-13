import os
import ipaddress
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-your-secret-key-here-changeme-in-production'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '10.3.224.188',
    '0.0.0.0',
    '172.18.0.1',
    '10.30.225.3',
]

# Добавляем диапазон 192.168.0.0/23 (от 192.168.0.0 до 192.168.1.255)
ALLOWED_HOSTS.extend([str(ip) for ip in ipaddress.IPv4Network('192.168.0.0/23')])

# Application definition

# Web Push
VAPID_PUBLIC_KEY = 'BPWzM8Sg21koEirpUOKjfqqqUeOL6c4PrF3KwT32QYT9pQP6R1Da9u8jSS0UMTkx4DL_75iOadzTAPNSOJVGlpo'
VAPID_PRIVATE_KEY = 'a4IVr9jA_SyFG-cohYOfztaM0Ul3xrXZI8qgl6a_KKk'
VAPID_ADMIN_EMAIL = 'mailto:webmaster@localhost'

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

LOGIN_URL = '/login/'  # URL для входа
LOGIN_REDIRECT_URL = '/profile/'  # Куда перенаправлять после входа
LOGOUT_REDIRECT_URL = '/'  # Куда перенаправлять после выхода

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True

# Session Persistence (Account stays saved for 1 year)
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
