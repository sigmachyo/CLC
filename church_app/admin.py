from django.contrib import admin
from .models import (
    Announcement, 
    HeroBackground, 
    Category, 
    Video, 
    BiblePlan, 
    BibleReading, 
    UserBibleProgress, 
    Event, 
    EventRegistration, 
    KidsContent, 
    KidsProgress, 
    DailyVerse, 
    PrayerRequest, 
    PushSubscription, 
    Donation, 
    News,
    PastorPhoto,
    HomeGroup
)

# ============================================
# Announcement Admin
# ============================================
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Содержание', {
            'fields': ('title', 'description', 'image')
        }),
        ('Настройки', {
            'fields': ('button_text', 'button_link', 'is_active', 'expires_at')
        }),
    )
    actions = ['broadcast_push']

    def broadcast_push(self, request, queryset):
        from .utils_push import broadcast_push_notification
        count = 0
        success_total = 0
        for announcement in queryset:
            payload = {
                'title': 'Новое объявление CLC',
                'body': announcement.title,
                'url': '/'
            }
            s, f = broadcast_push_notification(payload)
            success_total += s
            count += 1
        self.message_user(request, f'Отправлено пушей для {count} объявлений. Успешно: {success_total}.')
    broadcast_push.short_description = "Разослать Push-уведомление"


# ============================================
# HeroBackground Admin
# ============================================
@admin.register(HeroBackground)
class HeroBackgroundAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'link_url', 'created_at')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('title',)
    ordering = ('order', '-created_at')


# ============================================
# Category Admin
# ============================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'order', 'is_active')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')


# ============================================
# Video Admin
# ============================================
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'duration', 'views_count', 'is_featured', 'is_active')
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('title', 'description')
    ordering = ('-is_featured', 'order', '-created_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'category', 'thumbnail')
        }),
        ('Видео', {
            'fields': ('video_file', 'youtube_url', 'rutube_url', 'duration'),
            'description': 'Длительность указывается в секундах (напр. 3600 = 1 час)',
        }),
        ('Настройки', {
            'fields': ('is_featured', 'order', 'is_active')
        }),
    )


# ============================================
# BiblePlan Admin
# ============================================
@admin.register(BiblePlan)
class BiblePlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'days_count', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('order', 'title')


# ============================================
# BibleReading Admin
# ============================================
@admin.register(BibleReading)
class BibleReadingAdmin(admin.ModelAdmin):
    list_display = ('plan', 'day_number', 'title', 'bible_passage')
    list_filter = ('plan',)
    search_fields = ('title', 'bible_passage')
    ordering = ('plan', 'day_number')


# ============================================
# UserBibleProgress Admin
# ============================================
@admin.register(UserBibleProgress)
class UserBibleProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'current_day', 'get_progress_percentage', 'last_read_at')
    list_filter = ('plan',)
    search_fields = ('user__username', 'plan__title')


# ============================================
# Event Admin
# ============================================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'event_type', 'start_date', 'location', 'is_featured', 'is_active')
    list_filter = ('event_type', 'is_featured', 'is_active')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
    ordering = ('start_date',)
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'event_type', 'image')
        }),
        ('Дата и время', {
            'fields': ('start_date', 'end_date')
        }),
        ('Место проведения', {
            'fields': ('location', 'address')
        }),
        ('Дополнительно', {
            'fields': ('max_participants', 'is_featured', 'is_active')
        }),
    )


# ============================================
# EventRegistration Admin
# ============================================
@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at', 'is_confirmed', 'attended')
    list_filter = ('is_confirmed', 'attended', 'event')
    search_fields = ('user__username', 'event__title')
    date_hierarchy = 'registered_at'


# ============================================
# KidsContent Admin
# ============================================
@admin.register(KidsContent)
class KidsContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'age_group', 'views_count', 'is_featured', 'is_active')
    list_filter = ('content_type', 'age_group', 'is_featured', 'is_active')
    search_fields = ('title', 'description', 'bible_verse')
    ordering = ('-is_featured', 'order', '-created_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'content_type', 'age_group', 'thumbnail')
        }),
        ('Контент', {
            'fields': ('video_file', 'youtube_url', 'game_data', 'printable_material')
        }),
        ('Библейский стих', {
            'fields': ('bible_verse',)
        }),
        ('Настройки', {
            'fields': ('is_featured', 'order', 'is_active')
        }),
    )


# ============================================
# KidsProgress Admin
# ============================================
@admin.register(KidsProgress)
class KidsProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'completed', 'score', 'last_accessed')
    list_filter = ('completed', 'content__content_type')
    search_fields = ('user__username', 'content__title')


# ============================================
# DailyVerse Admin
# ============================================
@admin.register(DailyVerse)
class DailyVerseAdmin(admin.ModelAdmin):
    list_display = ('date', 'reference', 'verse_text')
    list_filter = ('date',)
    search_fields = ('verse_text', 'reference')
    ordering = ('-date',)


# ============================================
# PrayerRequest Admin (ОБНОВЛЁННЫЙ)
# ============================================
@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_answered', 'answered_at', 'prayer_count', 'is_public', 'created_at')
    list_filter = ('is_answered', 'is_public', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('answered_at',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'user')
        }),
        ('Статус', {
            'fields': ('is_answered', 'answered_at', 'prayer_count', 'is_public')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )


# ============================================
# PushSubscription Admin
# ============================================
@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint_snippet', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'endpoint')
    readonly_fields = ('endpoint', 'p256dh', 'auth', 'created_at')

    def endpoint_snippet(self, obj):
        return obj.endpoint[:40] + '...' if len(obj.endpoint) > 40 else obj.endpoint
    endpoint_snippet.short_description = 'Endpoint'


# ============================================
# Donation Admin
# ============================================
@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('amount', 'status', 'user', 'payment_id', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'payment_id')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('payment_id', 'created_at')


# ============================================
# News Admin
# ============================================
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_featured',
        'is_active',
        'created_at',
    )
    list_filter = (
        'is_featured',
        'is_active',
        'created_at',
    )
    search_fields = (
        'title',
        'short_description',
        'content',
    )
    prepopulated_fields = {
        'slug': ('title',)
    }
    ordering = ('-created_at',)


# ============================================
# PastorPhoto Admin
# ============================================
@admin.register(PastorPhoto)
class PastorPhotoAdmin(admin.ModelAdmin):
    list_display = ('slug', 'updated_at')
    search_fields = ('slug',)


# ============================================
# HomeGroup Admin
# ============================================
@admin.register(HomeGroup)
class HomeGroupAdmin(admin.ModelAdmin):
    list_display = ('district', 'address', 'get_type_display', 'get_day_display', 'time', 'get_age_display', 'is_active', 'order')
    list_filter = ('district', 'group_type', 'day', 'is_active')
    search_fields = ('district', 'address')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'district')
    fieldsets = (
        ('Основная информация', {
            'fields': ('district', 'address', 'group_type', 'is_active', 'order')
        }),
        ('Время проведения', {
            'fields': ('day', 'time')
        }),
        ('Возраст', {
            'fields': ('age_min', 'age_max', 'age_display')
        }),
    )