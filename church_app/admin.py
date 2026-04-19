from django.contrib import admin
from .models import Announcement

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

from .models import HeroBackground

@admin.register(HeroBackground)
class HeroBackgroundAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'link_url', 'created_at')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('title',)
    ordering = ('order', '-created_at')

from .models import Category, Video, BiblePlan, BibleReading, UserBibleProgress, Event, EventRegistration, KidsContent, KidsProgress, DailyVerse, PrayerRequest, PushSubscription

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'order', 'is_active')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

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
            'fields': ('video_file', 'youtube_url', 'duration')
        }),
        ('Настройки', {
            'fields': ('is_featured', 'order', 'is_active')
        }),
    )

@admin.register(BiblePlan)
class BiblePlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'days_count', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('order', 'title')

@admin.register(BibleReading)
class BibleReadingAdmin(admin.ModelAdmin):
    list_display = ('plan', 'day_number', 'title', 'bible_passage')
    list_filter = ('plan',)
    search_fields = ('title', 'bible_passage')
    ordering = ('plan', 'day_number')

@admin.register(UserBibleProgress)
class UserBibleProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'current_day', 'get_progress_percentage', 'last_read_at')
    list_filter = ('plan',)
    search_fields = ('user__username', 'plan__title')

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

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at', 'is_confirmed', 'attended')
    list_filter = ('is_confirmed', 'attended', 'event')
    search_fields = ('user__username', 'event__title')
    date_hierarchy = 'registered_at'

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

@admin.register(KidsProgress)
class KidsProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'completed', 'score', 'last_accessed')
    list_filter = ('completed', 'content__content_type')
    search_fields = ('user__username', 'content__title')

@admin.register(DailyVerse)
class DailyVerseAdmin(admin.ModelAdmin):
    list_display = ('date', 'reference', 'verse_text')
    list_filter = ('date',)
    search_fields = ('verse_text', 'reference')
    ordering = ('-date',)

@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_answered', 'prayer_count', 'is_public', 'created_at')
    list_filter = ('is_answered', 'is_public', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint_snippet', 'created_at')
    list_filter = ('created_at',)

    def endpoint_snippet(self, obj):
        return obj.endpoint[:40] + '...' if len(obj.endpoint) > 40 else obj.endpoint