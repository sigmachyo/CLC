from django.urls import path
from . import views, views_library, views_prayer, views_donate, views_chat, views_push

urlpatterns = [
    # Главная страница с таймером трансляции
    path('', views.home, name='home'),

    # Карта с уровнями (Путь)
    path('map/', views.index, name='index'),

    # Аутентификация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Профиль
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/change-password/', views.change_password_view, name='change_password'),

    # Уровни
    path('level/<int:level_id>/', views.level_detail, name='level_detail'),
    path('level/<int:level_id>/complete/', views.complete_level, name='complete_level'),

    # Объявления
    path('dismiss-announcement/', views.dismiss_announcement, name='dismiss_announcement'),

    # 📡 API: YouTube Live Stream (проксирует RSS без CORS)
    path('api/live-stream/', views.live_stream_api, name='live_stream_api'),

    # 📡 API: Rutube Fallback (если YouTube embed недоступен)
    path('api/rutube-stream/', views.rutube_stream_api, name='rutube_stream_api'),

    # 📡 API: Единый Video API (Rutube + YouTube fallback)
    path('api/video/', views.video_api, name='video_api'),

    # 🙏 Молитвенная стена
    path('prayer/', views_prayer.prayer_list, name='prayer_list'),
    path('prayer/add/', views_prayer.prayer_add, name='prayer_add'),
    path('prayer/<int:prayer_id>/support/', views_prayer.prayer_support, name='prayer_support'),
    path('prayer/my/', views_prayer.my_prayers, name='my_prayers'),
    path('prayer/<int:prayer_id>/toggle/', views_prayer.prayer_toggle_answered, name='prayer_toggle_answered'),

    # 💖 Пожертвования
    path('donate/', views_donate.donate_page, name='donate'),
    path('donate/gateway/<uuid:payment_id>/', views_donate.mock_payment_gateway, name='mock_payment_gateway'),
    path('donate/success/', views_donate.donate_success, name='donate_success'),
    path('donate/fail/', views_donate.donate_fail, name='donate_fail'),

    # 💬 Чаты и Форумы
    path('chat/', views_chat.chat_list_view, name='chat_list'),
    path('chat/<int:room_id>/', views_chat.chat_room_view, name='chat_room'),
    path('api/chat/<int:room_id>/send/', views_chat.api_send_message, name='api_chat_send'),
    path('api/chat/<int:room_id>/messages/', views_chat.api_get_messages, name='api_chat_messages'),

    # 📚 Библиотека
    path('library/', views_library.library_home, name='library_home'),
    path('library/category/<slug:category_slug>/', views_library.library_category, name='library_category'),
    path('library/video/<int:video_id>/', views_library.video_detail, name='video_detail'),

    # 📖 Библия и планы чтения
    path('library/bible/', views_library.bible_home, name='bible_home'),
    path('library/bible/plan/<int:plan_id>/', views_library.bible_plan_detail, name='bible_plan_detail'),
    path('library/bible/read/<int:plan_id>/<int:day>/', views_library.bible_read_day, name='bible_read_day'),
    path('library/bible/complete/<int:plan_id>/<int:day>/', views_library.complete_bible_day, name='complete_bible_day'),

    # 📅 События
    path('library/events/', views_library.events_list, name='events_list'),
    path('library/event/<int:event_id>/', views_library.event_detail, name='event_detail'),
    path('library/event/<int:event_id>/register/', views_library.event_register, name='event_register'),

    # 👶 Детский раздел
    path('library/kids/', views_library.kids_home, name='kids_home'),
    path('library/kids/<int:content_id>/', views_library.kids_content_detail, name='kids_content_detail'),
    # 🔔 Уведомления (Push API)
    path('api/push/subscribe/', views_push.subscribe, name='api_push_subscribe'),

    # PWA Offline fallback
    path('offline/', views.offline_view, name='offline'),
]