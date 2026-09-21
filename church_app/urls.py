from django.urls import path
from django.views.generic import TemplateView, RedirectView
from . import views, views_library, views_prayer, views_donate, views_push, views_auth

urlpatterns = [
    path('', views.home, name='home'),

    # Подтверждение Email через 6-значный OTP код
    path('accounts/verify-code/', views_auth.verify_otp_view, name='verify_otp'),
    path('accounts/resend-code/', views_auth.resend_otp_view, name='resend_otp'),
    path('accounts/api/check-username/', views_auth.check_username_api, name='api_check_username'),
    path('accounts/api/check-email/', views_auth.check_email_api, name='api_check_email'),

    # Обратная совместимость для ссылок login, register, logout
    path('login/', RedirectView.as_view(pattern_name='account_login', permanent=False), name='login'),
    path('register/', RedirectView.as_view(pattern_name='account_signup', permanent=False), name='register'),
    path('logout/', RedirectView.as_view(pattern_name='account_logout', permanent=False), name='logout'),
    path('password-reset/', RedirectView.as_view(pattern_name='account_reset_password', permanent=False), name='password_reset'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('profile/avatar/upload/', views.profile_avatar_upload, name='profile_avatar_upload'),
    path('user/<str:username>/', views.user_public_profile, name='user_public_profile'),

    # API молитвенных друзей и любимых стихов
    path('api/user/<str:username>/toggle-friend/', views.toggle_prayer_friend, name='toggle_prayer_friend'),
    path('api/verses/favorite/add/', views.add_favorite_verse, name='add_favorite_verse'),
    path('api/verses/favorite/<int:verse_id>/delete/', views.delete_favorite_verse, name='delete_favorite_verse'),

    path('dismiss-announcement/', views.dismiss_announcement, name='dismiss_announcement'),

    path('api/live-stream/', views.live_stream_api, name='live_stream_api'),
    path('api/rutube-stream/', views.rutube_stream_api, name='rutube_stream_api'),
    path('api/video/', views.video_api, name='video_api'),
    path('api/debug/stream-status/', views.debug_stream_status, name='debug_stream_status'),

    path('prayer/', views_prayer.prayer_list, name='prayer_list'),
    path('prayer/add/', views_prayer.prayer_add, name='prayer_add'),
    path('prayer/<int:prayer_id>/support/', views_prayer.prayer_support, name='prayer_support'),
    path('prayer/my/', views_prayer.my_prayers, name='my_prayers'),
    path('prayer/<int:prayer_id>/toggle/', views_prayer.prayer_toggle_answered, name='prayer_toggle_answered'),

    path('prayer/revelations/', views_prayer.revelation_list, name='revelation_list'),
    path('prayer/revelations/add/', views_prayer.revelation_add, name='revelation_add'),
    path('prayer/revelations/<int:pk>/react/', views_prayer.revelation_react, name='revelation_react'),

    path('donate/', views_donate.donate_page, name='donate'),
    path('donate/gateway/<uuid:payment_id>/', views_donate.mock_payment_gateway, name='mock_payment_gateway'),
    path('donate/success/', views_donate.donate_success, name='donate_success'),
    path('donate/fail/', views_donate.donate_fail, name='donate_fail'),

    path('library/', views_library.library_home, name='library_home'),
    path('library/videos/', views_library.video_list, name='video_list'),
    path('library/worship/', views_library.worship_songs_list, name='library_worship'),
    path('worship/', views_library.worship_songs_list, name='worship_songs'),
    path('library/category/<slug:category_slug>/', views_library.library_category, name='library_category'),
    path('library/video/<int:video_id>/', views_library.video_detail, name='video_detail'),

    path('library/bible/', views_library.bible_home, name='bible_home'),
    path('library/bible/plan/<int:plan_id>/', views_library.bible_plan_detail, name='bible_plan_detail'),
    path('library/bible/read/<int:plan_id>/<int:day>/', views_library.bible_read_day, name='bible_read_day'),
    path('library/bible/complete/<int:plan_id>/<int:day>/', views_library.complete_bible_day, name='complete_bible_day'),

    path('library/events/', views_library.events_list, name='events_list'),
    path('events/', views_library.events_list, name='events_catalog'),
    path('events/<slug:slug>/', views_library.event_detail, name='event_detail'),
    path('events/<slug:slug>/register/', views_library.event_register, name='event_register'),

    path('library/kids/', views_library.kids_home, name='kids_home'),
    path('library/kids/<int:content_id>/', views_library.kids_content_detail, name='kids_content_detail'),

    path('api/push/subscribe/', views_push.subscribe, name='api_push_subscribe'),
    path('api/push/test/', views_push.test_push, name='api_push_test'),

    path('offline/', views.offline_view, name='offline'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('favicon.ico', RedirectView.as_view(url='/static/icons/favicon.ico')),
    path('.well-known/appspecific/com.chrome.devtools.json', views.chrome_devtools_json),

    path('about/', views.about_view, name='about'),
    path('alpha/', TemplateView.as_view(template_name='info/alpha.html'), name='alpha'),
    path('ministries/', views.ministries_list_view, name='ministries'),
    path('ministries/<slug:slug>/', views.ministry_detail_view, name='ministry_detail'),
    path('api/ministries/<slug:slug>/apply/', views.apply_ministry_api, name='api_apply_ministry'),
    path('news/', views.news_list, name='news_list'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('calendar/', views.calendar_page_view, name='calendar'),
    path('home-meet/', views.home_meet_view, name='home_meet'),
    path('map/', views.community_map_view, name='community_map'),
    path('api/map/locations/', views.api_map_locations, name='api_map_locations'),
    path('regional-churches/', views.regional_churches_view, name='regional_churches'),
    path('privacy-policy/', TemplateView.as_view(template_name='info/privacy.html'), name='privacy'),
    path('api/upload-pastor-photo/', views.upload_pastor_photo, name='upload_pastor_photo'),
]