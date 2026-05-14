from django.urls import path
from django.views.generic import TemplateView, RedirectView
from . import views, views_library, views_prayer, views_donate, views_push

urlpatterns = [
    path('', views.home, name='home'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/change-password/', views.change_password_view, name='change_password'),

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

    path('donate/', views_donate.donate_page, name='donate'),
    path('donate/gateway/<uuid:payment_id>/', views_donate.mock_payment_gateway, name='mock_payment_gateway'),
    path('donate/success/', views_donate.donate_success, name='donate_success'),
    path('donate/fail/', views_donate.donate_fail, name='donate_fail'),

    path('library/', views_library.library_home, name='library_home'),
    path('library/category/<slug:category_slug>/', views_library.library_category, name='library_category'),
    path('library/video/<int:video_id>/', views_library.video_detail, name='video_detail'),

    path('library/bible/', views_library.bible_home, name='bible_home'),
    path('library/bible/plan/<int:plan_id>/', views_library.bible_plan_detail, name='bible_plan_detail'),
    path('library/bible/read/<int:plan_id>/<int:day>/', views_library.bible_read_day, name='bible_read_day'),
    path('library/bible/complete/<int:plan_id>/<int:day>/', views_library.complete_bible_day, name='complete_bible_day'),

    path('library/events/', views_library.events_list, name='events_list'),
    path('events/<slug:slug>/', views_library.event_detail, name='event_detail'),
    path('events/<slug:slug>/register/', views_library.event_register, name='event_register'),

    path('library/kids/', views_library.kids_home, name='kids_home'),
    path('library/kids/<int:content_id>/', views_library.kids_content_detail, name='kids_content_detail'),

    path('api/push/subscribe/', views_push.subscribe, name='api_push_subscribe'),

    path('offline/', views.offline_view, name='offline'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('favicon.ico', RedirectView.as_view(url='/static/icons/favicon.ico')),
    path('.well-known/appspecific/com.chrome.devtools.json', views.chrome_devtools_json),

    path('about/', TemplateView.as_view(template_name='info/about.html'), name='about'),
    path('alpha/', TemplateView.as_view(template_name='info/alpha.html'), name='alpha'),
    path('ministries/', TemplateView.as_view(template_name='info/ministries.html'), name='ministries'),
    path('news/', TemplateView.as_view(template_name='info/news.html'), name='news_list'),
    path('calendar/', TemplateView.as_view(template_name='info/calendar.html'), name='calendar'),
    path('home-meet/', TemplateView.as_view(template_name='info/home_meet.html'), name='home_meet'),
    path('regional-churches/', TemplateView.as_view(template_name='info/regional_churches.html'), name='regional_churches'),
    path('privacy-policy/', TemplateView.as_view(template_name='info/privacy.html'), name='privacy'),
]