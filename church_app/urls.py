from django.urls import path
from . import views

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

    # URL для библиотеки
    path('library/', views.library_home, name='library_home'),
    path('library/category/<slug:category_slug>/', views.library_category, name='library_category'),
    path('library/video/<int:video_id>/', views.video_detail, name='video_detail'),
    path('library/bible/', views.bible_home, name='bible_home'),
    path('library/bible/plan/<int:plan_id>/', views.bible_plan_detail, name='bible_plan_detail'),
    path('library/bible/read/<int:plan_id>/<int:day>/', views.bible_read_day, name='bible_read_day'),
    path('library/bible/complete/<int:plan_id>/<int:day>/', views.complete_bible_day, name='complete_bible_day'),
    path('library/events/', views.events_list, name='events_list'),
    path('library/event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('library/event/<int:event_id>/register/', views.event_register, name='event_register'),
    path('library/kids/', views.kids_home, name='kids_home'),
    path('library/kids/<int:content_id>/', views.kids_content_detail, name='kids_content_detail'),
]