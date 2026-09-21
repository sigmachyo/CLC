from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.admin import TabularInline, StackedInline
from django.db import models
from django.utils import timezone
from .models import (
    Announcement, 
    HeroBackground, 
    Category, 
    Video, 
    PodcastEpisode,
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
    HomeGroup,
    Revelation,
    RevelationReaction,
    UserProfile,
    FavoriteVerse,
    PrayerConnection,
    Ministry,
    MinistryApplication,
)

# ============================================
# Announcement Admin
# ============================================
@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin):
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
class HeroBackgroundAdmin(ModelAdmin):
    list_display = ('preview', 'title', 'get_type_badge', 'is_active', 'order', 'link_url', 'created_at')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('title', 'video_url', 'link_url')
    ordering = ('order', '-created_at')

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 70px; height: 40px; object-fit: cover; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"/>', obj.image.url)
        if obj.video_url:
            return format_html('<span style="display:inline-flex; align-items:center; justify-content:center; width: 70px; height: 40px; background:#1e293b; color:#38bdf8; border-radius:6px; font-size:11px; font-weight:bold;">▶ MP4</span>')
        return format_html('<span style="color:#94a3b8;">—</span>')
    preview.short_description = "Превью"

    def get_type_badge(self, obj):
        if obj.video_url:
            return format_html('<span style="background:#e0f2fe; color:#0369a1; padding:3px 8px; border-radius:999px; font-size:12px; font-weight:600;">🎬 Видео</span>')
        return format_html('<span style="background:#f1f5f9; color:#475569; padding:3px 8px; border-radius:999px; font-size:12px; font-weight:600;">🖼️ Картинка</span>')
    get_type_badge.short_description = "Тип"


# ============================================
# Category Admin
# ============================================
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'category_type', 'order', 'is_active')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')


# ============================================
# Video Admin
# ============================================
@admin.register(Video)
class VideoAdmin(ModelAdmin):
    list_display = ('preview_thumb', 'title', 'category', 'get_source_badges', 'get_duration_pretty', 'views_count', 'is_featured', 'is_active')
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('title', 'description', 'youtube_url', 'rutube_url', 'vk_url')
    ordering = ('-is_featured', 'order', '-created_at')
    actions = ['sync_from_cloud', 'mark_featured', 'mark_active']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'category', 'thumbnail')
        }),
        ('Облачные видео (RuTube, YouTube, VK)', {
            'fields': ('rutube_url', 'vk_url', 'youtube_url', 'video_file', 'duration'),
            'description': 'Видео воспроизводятся во встроенном плеере из облака без нагрузки на сервер. Длительность указывается в секундах.',
        }),
        ('Настройки отображения', {
            'fields': ('is_featured', 'order', 'is_active', 'views_count')
        }),
    )

    def preview_thumb(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="width: 76px; height: 44px; object-fit: cover; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.15);"/>', obj.thumbnail.url)
        return format_html('<div style="width: 76px; height: 44px; background: #1e293b; color: #94a3b8; display:flex; align-items:center; justify-content:center; border-radius:6px; font-size:10px;">НЕТ ФОТО</div>')
    preview_thumb.short_description = "Обложка"

    def get_source_badges(self, obj):
        badges = []
        has_yt = bool(obj.youtube_url)
        has_rt = bool(obj.rutube_url)
        has_vk = bool(obj.vk_url)
        if has_yt and has_rt and has_vk:
            return format_html('<span style="background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 700;">⚡ RuTube + YouTube + VK</span>')
        if has_rt:
            badges.append('<span style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600;">🔵 RuTube</span>')
        if has_vk:
            badges.append('<span style="background: #eff6ff; color: #2787F5; border: 1px solid #93c5fd; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600;">🔷 VK</span>')
        if has_yt:
            badges.append('<span style="background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600;">🔴 YouTube</span>')
        if obj.video_file:
            badges.append('<span style="background: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600;">📁 Файл</span>')
        return format_html(' '.join(badges)) if badges else format_html('<span style="color:#94a3b8;">—</span>')
    get_source_badges.short_description = "Источник"

    def get_duration_pretty(self, obj):
        display = obj.get_duration_display()
        return display if display else '—'
    get_duration_pretty.short_description = "Длительность"

    @admin.action(description="🔄 Синхронизировать с RuTube, YouTube и VK")
    def sync_from_cloud(self, request, queryset):
        from church_app.services_video_sync import sync_videos
        stats = sync_videos()
        self.message_user(request, f"Синхронизация завершена: +{stats['new_count']} новых, {stats['merged_count']} дубликатов объединено. Всего видео: {stats['total']}.")

    @admin.action(description="⭐ Сделать рекомендуемыми")
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="✅ Активировать выбранные")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)


# ============================================
# PodcastEpisode Admin
# ============================================
@admin.register(PodcastEpisode)
class PodcastEpisodeAdmin(ModelAdmin):
    list_display = ('title', 'speaker', 'duration', 'order', 'is_active', 'listen_link')
    list_filter = ('is_active', 'speaker')
    search_fields = ('title', 'speaker')
    ordering = ('order', 'id')
    actions = ['sync_from_rss', 'mark_active']

    def listen_link(self, obj):
        if obj.audio_url:
            return format_html(
                '<a href="{}" target="_blank" style="background:#0284c7; color:#fff; padding:3px 10px; border-radius:999px; text-decoration:none; font-size:11px; font-weight:600; display:inline-flex; align-items:center; gap:4px;">'
                '▶ MP3</a>',
                obj.audio_url
            )
        return '—'
    listen_link.short_description = "Аудио"

    @admin.action(description="🔄 Синхронизировать с Podster RSS")
    def sync_from_rss(self, request, queryset):
        from church_app.services_podcast_sync import sync_podcasts
        stats = sync_podcasts()
        self.message_user(request, f"Синхронизация подкастов завершена: +{stats['new_count']} новых, {stats['updated_count']} обновлено. Всего: {stats['total']}.")

    @admin.action(description="✅ Активировать выбранные")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)


# (BiblePlan, BibleReading, UserBibleProgress removed from admin as reading plans are disabled)


# ============================================
# Event Admin
# ============================================
# Event Admin & CMS Builder
# ============================================
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Event, EventBlock, EventRegistration

class EventBlockInline(TabularInline):
    model = EventBlock
    extra = 0
    ordering = ('order',)
    fields = ('block_type', 'order', 'is_active', 'content')

class EventStatusFilter(admin.SimpleListFilter):
    title = 'Статус даты'
    parameter_name = 'date_status'

    def lookups(self, request, model_admin):
        return (
            ('upcoming', '🟢 Предстоящие / Актуальные'),
            ('past', '⚪ Прошедшие'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'upcoming':
            return queryset.filter(
                models.Q(end_date__gte=now) | (models.Q(end_date__isnull=True) & models.Q(start_date__gte=now))
            )
        if self.value() == 'past':
            return queryset.filter(
                models.Q(end_date__lt=now) | (models.Q(end_date__isnull=True) & models.Q(start_date__lt=now))
            )
        return queryset

@admin.register(Event)
class EventAdmin(ModelAdmin):
    inlines = [EventBlockInline]
    list_display = ('title', 'builder_link', 'slug', 'event_type', 'start_date', 'get_event_status', 'is_conference', 'is_featured', 'is_active')
    list_filter = (EventStatusFilter, 'is_conference', 'event_type', 'is_featured', 'is_active')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
    ordering = ('start_date',)
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'event_type', 'is_conference', 'image')
        }),
        ('Дата и время', {
            'fields': ('start_date', 'end_date')
        }),
        ('Место проведения и трансляция', {
            'fields': ('location', 'address', 'stream_link')
        }),
        ('Пожертвование и реквизиты конференции', {
            'fields': ('registration_fee', 'sbp_url', 'paypal_url', 'support_telegram')
        }),
        ('Дополнительно', {
            'fields': ('max_participants', 'is_featured', 'is_active')
        }),
    )

    def get_event_status(self, obj):
        now = timezone.now()
        is_past = (obj.end_date and obj.end_date < now) or (not obj.end_date and obj.start_date < now)
        if is_past:
            return format_html('<span style="background: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600;">Прошедшее</span>')
        return format_html('<span style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600;">🟢 Предстоящее</span>')
    get_event_status.short_description = "Статус"

    def builder_link(self, obj):
        url = f"/admin/church_app/event/{obj.id}/builder/"
        return format_html(
            '<a href="{}" style="background:#c9a84c; color:#1a1f36; padding:4px 10px; border-radius:8px; font-weight:bold; text-decoration:none; font-size:12px; display:inline-flex; align-items:center; gap:4px;">'
            '✨ CMS Конструктор</a>',
            url
        )
    builder_link.short_description = "Конструктор лендинга"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:event_id>/builder/', self.admin_site.admin_view(self.builder_view), name='event_builder'),
        ]
        return custom_urls + urls

    def builder_view(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        if not event.slug:
            event.save()

        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'save_theme':
                event.theme_config = event.theme_config or {}
                event.theme_config['theme'] = request.POST.get('theme', 'clean_light')
                event.theme_config['hero_height'] = request.POST.get('hero_height', 'fullscreen')
                event.theme_config['accent_color'] = request.POST.get('accent_color', '#2563eb')
                event.theme_config['bg_color'] = request.POST.get('bg_color', '').strip()
                event.theme_config['font_family'] = request.POST.get('font_family', 'sans')
                event.theme_config['custom_css'] = request.POST.get('custom_css', '')
                event.theme_config['custom_head_html'] = request.POST.get('custom_head_html', '')
                event.theme_config['full_page_html'] = request.POST.get('full_page_html', '')
                event.save(update_fields=['theme_config'])
                messages.success(request, '🎨 Настройки темы и оформление успешно сохранены!')

            elif action == 'save_full_page_code':
                event.theme_config = event.theme_config or {}
                event.theme_config['full_page_html'] = request.POST.get('full_page_html', '')
                event.theme_config['custom_css'] = request.POST.get('custom_css', '')
                event.save(update_fields=['theme_config'])
                messages.success(request, '💻 Исходный код всей страницы успешно сохранен!')

            elif action == 'auto_generate':
                event.blocks.all().delete()
                # 1. Hero block (full screen)
                EventBlock.objects.create(
                    event=event, block_type='hero', order=1, is_active=True,
                    content={
                        'badge': 'Конференция / Школа',
                        'title': event.title,
                        'subtitle': event.description or 'Главное событие сезона. Вдохновение, общение и слово в силе.',
                        'banner_url': (event.image.url if event.image else ''),
                        'what_text': event.title,
                        'when_text': f"{event.start_date.strftime('%d.%m.%Y')} — {event.end_date.strftime('%d.%m.%Y')}",
                        'where_text': event.location or 'Онлайн-трансляция / Церковь KCLC',
                        'price_text': event.registration_fee or 'Добровольное пожертвование'
                    }
                )
                # 2. Concept / About
                EventBlock.objects.create(
                    event=event, block_type='concept', order=2, is_active=True,
                    content={
                        'title': 'О СОБЫТИИ',
                        'subtitle': 'Видение и цели',
                        'text_1': event.description or 'Это время духовного обновления, глубокого погружения и новых откровений.',
                        'text_2': 'Каждый участник получит практические инструменты и вдохновение для служения и жизни.'
                    }
                )
                # 3. Audience
                EventBlock.objects.create(
                    event=event, block_type='audience', order=3, is_active=True,
                    content={
                        'title': 'Для кого это событие',
                        'subtitle': 'Участники',
                        'cards': [
                            {'num': '01', 'title': 'Для служителей и лидеров', 'desc': 'Кто хочет расти в призвании и вести команды.'},
                            {'num': '02', 'title': 'Для молодежи и семей', 'desc': 'Кто ищет живого Божьего присутствия и ответов на важные вопросы.'},
                            {'num': '03', 'title': 'Для всех ищущих Бога', 'desc': 'Время открыть новую глубину веры и личных отношений с Творцом.'}
                        ]
                    }
                )
                # 4. Schedule
                EventBlock.objects.create(
                    event=event, block_type='schedule', order=4, is_active=True,
                    content={
                        'title': 'Расписание программы',
                        'subtitle': 'Тайминг сессий',
                        'sessions': [
                            {'day': 'День 1', 'time': '18:00–21:00 МСК', 'title': 'Открытие, хвала и ключевое слово'},
                            {'day': 'День 2', 'time': '10:00–14:00 МСК', 'title': 'Практические модули и мастер-классы'},
                            {'day': 'День 2', 'time': '18:00–21:00 МСК', 'title': 'Вечер хвалы, молитвы и благословения'}
                        ]
                    }
                )
                # 5. Speakers
                EventBlock.objects.create(
                    event=event, block_type='speakers', order=5, is_active=True,
                    content={
                        'title': 'Спикеры и наставники',
                        'subtitle': 'Команда служения',
                        'speakers': [
                            {'name': 'Пастор церкви', 'role': 'Старший служитель', 'initials': 'ПЦ', 'bio': 'Служение словом, молитвой и душепопечением.'}
                        ]
                    }
                )
                # 6. Pricing & Requisites
                EventBlock.objects.create(
                    event=event, block_type='pricing', order=6, is_active=True,
                    content={
                        'title': 'Регистрационный взнос и реквизиты',
                        'sbp_amount': event.registration_fee or '1 000 ₽',
                        'sbp_url': event.sbp_url or '',
                        'paypal_amount': '30 €',
                        'paypal_url': event.paypal_url or '',
                        'support_telegram': event.support_telegram or '@krasnkate'
                    }
                )
                # 7. Registration
                EventBlock.objects.create(
                    event=event, block_type='registration', order=7, is_active=True,
                    content={
                        'title': 'Регистрация на конференцию',
                        'subtitle': 'Заполните форму и прикрепите чек. Билет придет на email.'
                    }
                )
                # 8. FAQ
                EventBlock.objects.create(
                    event=event, block_type='faq', order=8, is_active=True,
                    content={
                        'title': 'Часто задаваемые вопросы',
                        'faq_items': [
                            {'question': 'Как получить доступ к трансляции?', 'answer': 'Ссылка и билет придут на ваш e-mail после регистрации.'},
                            {'question': 'Будет ли доступна запись?', 'answer': 'Да, все зарегистрированные участники получат доступ к материалам.'}
                        ]
                    }
                )
                event.is_conference = True
                event.theme_config = event.theme_config or {}
                if not event.theme_config.get('theme'):
                    event.theme_config['theme'] = 'clean_light'
                if not event.theme_config.get('hero_height'):
                    event.theme_config['hero_height'] = 'fullscreen'
                event.save()
                messages.success(request, '⚡ Полная визитка конференции автоматически сгенерирована!')

            elif action == 'generate_template':
                template_type = request.POST.get('template_type')
                if template_type == 'zvuki_nebes':
                    event.blocks.all().delete()
                    # 1. Hero
                    EventBlock.objects.create(
                        event=event, block_type='hero', order=1, is_active=True,
                        content={
                            'badge': 'Практическая онлайн-школа',
                            'title': 'Онлайн-школа «Звуки небес» с Деном МакКоллам и Бефани Хикс',
                            'subtitle': 'Практическая онлайн-школа для пасторов, служителей и команд прославления о том, как приносить Небеса на землю и высвобождать Божью волю там, куда Он тебя поместил.',
                            'banner_url': '',
                            'what_text': 'Онлайн-школа пророческого служения и поклонения',
                            'when_text': '23–25 апреля 2026 • 18:00–20:00 МСК',
                            'where_text': 'Закрытый прямой эфир в Zoom + записи',
                            'price_text': 'по СБП 5 000 ₽ / PayPal 60 €',
                            'featured_speakers': [
                                {'name': 'Дэн МакКоллам', 'role': 'Спикер школы', 'initials': 'ДМ'},
                                {'name': 'Бефани Хикс', 'role': 'Спикер школы', 'initials': 'БХ'},
                            ]
                        }
                    )
                    # 2. Concept
                    EventBlock.objects.create(
                        event=event, block_type='concept', order=2, is_active=True,
                        content={
                            'title': 'НЕБО ИМЕЕТ ГОЛОС',
                            'subtitle': 'Видение и призвание',
                            'text_1': 'Бог поместил тебя в определённом месте, городе, церкви и окружении не случайно. Он желает действовать через Своих людей — через поклонение, согласие, веру и готовность сказать Ему своё «ДА».',
                            'text_2': 'Как распознать то, что Небо говорит сейчас? Как не просто услышать Божью волю, но согласиться с ней и высвободить её на своей территории?',
                        }
                    )
                    # 3. Audience
                    EventBlock.objects.create(
                        event=event, block_type='audience', order=3, is_active=True,
                        content={
                            'title': 'Для кого эта школа',
                            'subtitle': 'Целевая аудитория',
                            'cards': [
                                {'num': '01', 'title': 'Для пасторов', 'desc': 'Которые хотят глубже понимать, как Церковь может слышать Божий голос и воплощать Его волю на своей территории.'},
                                {'num': '02', 'title': 'Для лидеров и служителей', 'desc': 'Которые хотят научиться различать голос Небес и действовать в согласии с тем, что делает Бог в этом сезоне.'},
                                {'num': '03', 'title': 'Для команд прославления', 'desc': 'Которые хотят идти глубже привычного формата поклонения и понимать пророческое измерение музыкального служения.'},
                                {'num': '04', 'title': 'Для тех, кто хочет большего', 'desc': 'Не просто знать о Божьем присутствии, но сотрудничать с Небом в повседневной жизни, призвании и служении.'},
                            ]
                        }
                    )
                    # 4. Topics
                    EventBlock.objects.create(
                        event=event, block_type='topics', order=4, is_active=True,
                        content={
                            'title': 'Ключевые темы',
                            'subtitle': 'Программа школы',
                            'topics': [
                                {'num': '01', 'title': 'Небеса на земле', 'desc': 'Практический путь к тому, чтобы приносить реальность Небес туда, куда Бог поместил тебя.'},
                                {'num': '02', 'title': 'Голос Небес', 'desc': 'Как слышать то, что говорит Бог, распознавать Его движение и становиться Его голосом.'},
                                {'num': '03', 'title': 'Пророческое поклонение', 'desc': 'Как поклонение становится пространством согласия с Небом.'},
                                {'num': '04', 'title': 'Песнь Господа и голос народа', 'desc': 'Как соединяется то, что высвобождает Небо, с голосом поклоняющейся Церкви.'},
                                {'num': '05', 'title': 'Твое «ДА» Богу', 'desc': 'Почему наше согласие, послушание и готовность имеют значение.'},
                                {'num': '06', 'title': 'Голос Небес через Церковь', 'desc': 'Как Церкви становиться живым выражением Божьей воли для своего города.'},
                            ]
                        }
                    )
                    # 5. Schedule
                    EventBlock.objects.create(
                        event=event, block_type='schedule', order=5, is_active=True,
                        content={
                            'title': 'Расписание школы',
                            'subtitle': 'Прямой эфир в Zoom и записи сессий',
                            'days': [
                                {'day': 'Четверг, 23 апреля', 'sessions': [{'time': '18:00–20:00 МСК', 'title': 'Небеса на земле и Голос Небес'}]},
                                {'day': 'Пятница, 24 апреля', 'sessions': [{'time': '18:00–20:00 МСК', 'title': 'Пророческое поклонение и Песнь Господа'}]},
                                {'day': 'Суббота, 25 апреля', 'sessions': [{'time': '18:00–20:00 МСК', 'title': 'Голос Небес через Церковь и Активация'}]},
                            ]
                        }
                    )
                    # 6. Speakers
                    EventBlock.objects.create(
                        event=event, block_type='speakers', order=6, is_active=True,
                        content={
                            'title': 'Спикеры школы',
                            'subtitle': 'Наставники и служители',
                            'speakers': [
                                {
                                    'name': 'Дэн МакКоллам (Dan McCollam)',
                                    'role': 'Спикер школы',
                                    'initials': 'ДМ',
                                    'bio': 'Пророческий служитель, автор, спикер и тренер международного уровня. Соучредитель Bethel School of the Prophets (Реддинг, Калифорния) и основатель Prophetic Company Global — международного сообщества тренеров, обучающих людей слышать голос Бога и действовать в пророческом даре. Основатель Sounds of the Nations.',
                                    'books': 'Автор более 25 книг, включая «Пророческое сообщество», «Базовая подготовка к пророческой активации» и «Добрая битва».',
                                },
                                {
                                    'name': 'Бефани Хикс (Bethany Hicks)',
                                    'role': 'Спикер школы',
                                    'initials': 'БХ',
                                    'bio': 'Соучредитель Prophetic Company Global, международный спикер, автор и признанный тренер. Обучает слышать голос Бога практично, доступно и современно, уделяя особое внимание пророческому искусству, поклонению и активации духовных даров.',
                                    'books': 'Автор ряда обучающих курсов и пособий по активации пророческого служения в церкви и в жизни.',
                                }
                            ]
                        }
                    )
                    # 7. Pricing
                    EventBlock.objects.create(
                        event=event, block_type='pricing', order=7, is_active=True,
                        content={
                            'title': 'Регистрационный взнос и реквизиты',
                            'subtitle': 'Внесение добровольного пожертвования',
                            'sbp_amount': '5 000 ₽',
                            'sbp_url': 'https://qr.nspk.ru/AS1A003KDIQAGT8J9TP836SFB4M5TEPQ?type=01&bank=100000000111&crc=E94F',
                            'paypal_amount': '60 €',
                            'paypal_url': 'https://www.paypal.me/ElenaAshaeva',
                            'support_telegram': '@krasnkate',
                        }
                    )
                    # 8. Registration
                    EventBlock.objects.create(
                        event=event, block_type='registration', order=8, is_active=True,
                        content={
                            'title': 'Регистрация на школу',
                            'subtitle': 'Заполните форму для участия и получения электронного билета',
                        }
                    )
                    event.is_conference = True
                    event.registration_fee = 'по СБП — 5000 руб / PayPal — 60 евро'
                    event.sbp_url = 'https://qr.nspk.ru/AS1A003KDIQAGT8J9TP836SFB4M5TEPQ?type=01&bank=100000000111&crc=E94F'
                    event.paypal_url = 'https://www.paypal.me/ElenaAshaeva'
                    event.support_telegram = '@krasnkate'
                    event.save()
                    messages.success(request, '✨ Полная презентационная структура «Звуки Небес» успешно создана!')

                elif template_type == 'worship_conf':
                    event.blocks.all().delete()
                    EventBlock.objects.create(
                        event=event, block_type='hero', order=1, is_active=True,
                        content={
                            'badge': 'Конференция поклонения',
                            'title': event.title,
                            'subtitle': event.description or 'Время обновления, глубокого поклонения в Духе и Истине и объединения сердец перед Богом.',
                            'what_text': 'Конференция хвалы и поклонения',
                            'when_text': f"{event.start_date.strftime('%d.%m.%Y')}",
                            'where_text': event.location or 'Церковь KCLC',
                            'price_text': '1 500 ₽'
                        }
                    )
                    EventBlock.objects.create(
                        event=event, block_type='concept', order=2, is_active=True,
                        content={
                            'title': 'ОГОНЬ НА ЖЕРТВЕННИКЕ',
                            'subtitle': 'Сердце поклонника',
                            'text_1': 'Поклонение — это не просто песни. Это образ жизни, открывающий небеса над нашими городами.',
                            'text_2': 'Бог ищет истинных поклонников, которые поклоняются Отцу в Духе и Истине.',
                        }
                    )
                    EventBlock.objects.create(
                        event=event, block_type='topics', order=3, is_active=True,
                        content={
                            'title': 'Темы конференции',
                            'topics': [
                                {'num': '01', 'title': 'Священство поклонника', 'desc': 'Призвание стоять в проломе за народ.'},
                                {'num': '02', 'title': 'Музыкальное мастерство и помазание', 'desc': 'Слияние профессионализма и духа.'},
                                {'num': '03', 'title': 'Спонтанная хвала', 'desc': 'Песнь Господня в реальном времени.'},
                            ]
                        }
                    )
                    EventBlock.objects.create(
                        event=event, block_type='pricing', order=4, is_active=True,
                        content={
                            'title': 'Условия участия',
                            'sbp_amount': '1 500 ₽',
                            'support_telegram': event.support_telegram or '@krasnkate',
                        }
                    )
                    EventBlock.objects.create(
                        event=event, block_type='registration', order=5, is_active=True,
                        content={'title': 'Регистрация участников'}
                    )
                    event.is_conference = True
                    event.save()
                    messages.success(request, '✨ Шаблон конференции поклонения успешно применен!')

                elif template_type == 'youth_conf':
                    event.blocks.all().delete()
                    EventBlock.objects.create(
                        event=event, block_type='hero', order=1, is_active=True,
                        content={
                            'badge': 'Молодежная конференция',
                            'title': event.title,
                            'subtitle': event.description or 'Новое поколение, горящее для Бога. Твой шаг веры и призвания.',
                            'what_text': 'Молодежный саммит',
                            'when_text': f"{event.start_date.strftime('%d.%m.%Y')}",
                            'where_text': event.location or 'KCLC Youth',
                            'price_text': 'Бесплатно'
                        }
                    )
                    EventBlock.objects.create(
                        event=event, block_type='audience', order=2, is_active=True,
                        content={
                            'title': 'Для кого эта конференция',
                            'cards': [
                                {'num': '01', 'title': 'Подростки и молодежь', 'desc': 'От 14 до 28 лет, ищущие свое призвание в Боге.'},
                                {'num': '02', 'title': 'Молодежные лидеры', 'desc': 'Команды служителей и наставников молодежи.'},
                            ]
                        }
                    )
                    EventBlock.objects.create(
                        event=event, block_type='pricing', order=3, is_active=True,
                        content={
                            'title': 'Регистрация',
                            'sbp_amount': 'Бесплатно / добровольный взнос',
                            'support_telegram': event.support_telegram or '@krasnkate',
                        }
                    )
                    EventBlock.objects.create(
                        event=event, block_type='registration', order=4, is_active=True,
                        content={'title': 'Регистрация на конференцию'}
                    )
                    event.is_conference = True
                    event.save()
                    messages.success(request, '✨ Шаблон молодежной конференции успешно применен!')

            elif action == 'upload_banner':
                if 'event_banner_file' in request.FILES:
                    event.image = request.FILES['event_banner_file']
                    event.save()
                    hero_b = event.blocks.filter(block_type='hero').first()
                    if hero_b:
                        hero_b.content['banner_url'] = event.image.url
                        hero_b.save()
                    messages.success(request, '🖼️ Баннер события успешно загружен и применен!')
                else:
                    messages.warning(request, 'Файл баннера не выбран.')

            elif action == 'add_block':
                new_block_type = request.POST.get('new_block_type', 'concept')
                max_order = event.blocks.aggregate(models.Max('order'))['order__max'] or 0
                default_content = {}
                if new_block_type == 'hero':
                    default_content = {
                        'badge': 'Конференция',
                        'title': event.title,
                        'subtitle': event.description or '',
                        'banner_url': (event.image.url if event.image else ''),
                        'what_text': event.title,
                        'when_text': f"{event.start_date.strftime('%d.%m.%Y')}",
                        'where_text': event.location or 'Онлайн / KCLC',
                        'price_text': event.registration_fee or 'Добровольный взнос'
                    }
                elif new_block_type == 'concept':
                    default_content = {'title': 'О СОБЫТИИ', 'subtitle': 'Видение и цели', 'text_1': 'Описание цели и видения события.', 'text_2': ''}
                elif new_block_type == 'audience':
                    default_content = {'title': 'Для кого это событие', 'cards': [{'num': '01', 'title': 'Для всех желающих', 'desc': 'Описание целевой аудитории.'}]}
                elif new_block_type == 'topics':
                    default_content = {'title': 'Ключевые темы', 'topics': [{'num': '01', 'title': 'Тема 1', 'desc': 'Описание темы.'}]}
                elif new_block_type == 'schedule':
                    default_content = {'title': 'Расписание', 'sessions': [{'day': 'День 1', 'time': '18:00–20:00 МСК', 'title': 'Открытие'}]}
                elif new_block_type == 'speakers':
                    default_content = {'title': 'Спикеры', 'speakers': [{'name': 'Имя Спикера', 'role': 'Служитель', 'initials': 'ИС', 'bio': 'Описание'}]}
                elif new_block_type == 'pricing':
                    default_content = {'title': 'Регистрационный взнос и реквизиты', 'sbp_amount': '1 000 ₽', 'support_telegram': '@krasnkate'}
                elif new_block_type == 'registration':
                    default_content = {'title': 'Регистрация на событие', 'subtitle': 'Заполните форму для участия'}
                elif new_block_type == 'faq':
                    default_content = {'title': 'Часто задаваемые вопросы', 'faq_items': [{'question': 'Как принять участие?', 'answer': 'Заполните форму регистрации.'}]}
                elif new_block_type == 'video':
                    default_content = {'title': 'Трейлер события', 'video_url': '', 'caption': 'Смотрите видео-анонс'}
                elif new_block_type == 'text':
                    default_content = {'title': 'Заголовок раздела', 'lead': 'Вводный тезис или акцентная мысль.', 'body': 'Основной текст блока...', 'quote': ''}
                elif new_block_type == 'custom_html':
                    default_content = {
                        'title': 'Кастомный HTML / CSS блок',
                        'html': '<div class="custom-card">\n  <h3>Свой блок</h3>\n  <p>Произвольный контент, виджет или верстка.</p>\n</div>',
                        'css': '.custom-card { padding: 30px; border-radius: 20px; background: #f8fafc; border: 1px solid #e2e8f0; text-align: center; }'
                    }

                EventBlock.objects.create(
                    event=event, block_type=new_block_type, order=max_order + 1, is_active=True, content=default_content
                )
                event.is_conference = True
                event.save()
                messages.success(request, f'➕ Слайд/блок «{new_block_type}» успешно добавлен.')

            elif action == 'duplicate_block':
                block_id = request.POST.get('block_id')
                source = EventBlock.objects.filter(id=block_id, event=event).first()
                if source:
                    import copy
                    max_order = event.blocks.aggregate(models.Max('order'))['order__max'] or 0
                    EventBlock.objects.create(
                        event=event,
                        block_type=source.block_type,
                        order=max_order + 1,
                        is_active=True,
                        content=copy.deepcopy(source.content)
                    )
                    messages.success(request, f'📑 Слайд «{source.get_block_type_display()}» успешно продублирован!')

            elif action == 'add_custom_code':
                code = request.POST.get('custom_code_html', '').strip()
                custom_css = request.POST.get('custom_code_css', '').strip()
                title = request.POST.get('custom_code_title', '').strip() or 'Кастомный элемент'
                if code or custom_css:
                    max_order = event.blocks.aggregate(models.Max('order'))['order__max'] or 0
                    EventBlock.objects.create(
                        event=event, block_type='custom_html', order=max_order + 1, is_active=True,
                        content={'title': title, 'html': code, 'css': custom_css}
                    )
                    event.is_conference = True
                    event.save()
                    messages.success(request, '💻 Кастомный элемент успешно добавлен!')

            elif action == 'delete_block':
                block_id = request.POST.get('block_id')
                EventBlock.objects.filter(id=block_id, event=event).delete()
                for idx, b in enumerate(event.blocks.all().order_by('order'), 1):
                    b.order = idx
                    b.save(update_fields=['order'])
                messages.success(request, '🗑️ Слайд/блок успешно удален.')

            elif action == 'move_block':
                block_id = request.POST.get('block_id')
                direction = request.POST.get('direction')
                current_block = EventBlock.objects.filter(id=block_id, event=event).first()
                if current_block:
                    all_blocks = list(event.blocks.all().order_by('order'))
                    idx = all_blocks.index(current_block)
                    if direction == 'up' and idx > 0:
                        neighbor = all_blocks[idx - 1]
                        current_block.order, neighbor.order = neighbor.order, current_block.order
                        current_block.save(update_fields=['order'])
                        neighbor.save(update_fields=['order'])
                    elif direction == 'down' and idx < len(all_blocks) - 1:
                        neighbor = all_blocks[idx + 1]
                        current_block.order, neighbor.order = neighbor.order, current_block.order
                        current_block.save(update_fields=['order'])
                        neighbor.save(update_fields=['order'])
                    messages.success(request, 'Порядок слайдов обновлен.')

            elif action == 'save_blocks':
                # Проверяем, был ли загружен файл баннера
                if 'event_banner_file' in request.FILES:
                    event.image = request.FILES['event_banner_file']
                    event.save()

                import json
                for block in event.blocks.all():
                    is_active = f'block_{block.id}_active' in request.POST
                    block.is_active = is_active

                    # Настройки расположения и оформления слайда
                    block.content['text_align'] = request.POST.get(f'block_{block.id}_text_align', block.content.get('text_align', 'center'))
                    block.content['bg_style'] = request.POST.get(f'block_{block.id}_bg_style', block.content.get('bg_style', 'default'))

                    # Прямой кастомный HTML/CSS для этого слайда (Code mode)
                    custom_html_override = request.POST.get(f'block_{block.id}_custom_html_override', '')
                    if custom_html_override.strip():
                        block.content['custom_html_override'] = custom_html_override.strip()
                    elif f'block_{block.id}_custom_html_override' in request.POST:
                        block.content.pop('custom_html_override', None)

                    custom_css_val = request.POST.get(f'block_{block.id}_custom_css', '').strip()
                    if custom_css_val:
                        block.content['custom_css'] = custom_css_val
                    elif f'block_{block.id}_custom_css' in request.POST:
                        block.content.pop('custom_css', None)

                    # Обработка по типам блоков
                    if block.block_type == 'hero':
                        block.content['badge'] = request.POST.get(f'block_{block.id}_badge', block.content.get('badge', ''))
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        block.content['subtitle'] = request.POST.get(f'block_{block.id}_subtitle', block.content.get('subtitle', ''))
                        block.content['what_text'] = request.POST.get(f'block_{block.id}_what_text', block.content.get('what_text', ''))
                        block.content['when_text'] = request.POST.get(f'block_{block.id}_when_text', block.content.get('when_text', ''))
                        block.content['where_text'] = request.POST.get(f'block_{block.id}_where_text', block.content.get('where_text', ''))
                        block.content['price_text'] = request.POST.get(f'block_{block.id}_price_text', block.content.get('price_text', ''))
                        banner_url_val = request.POST.get(f'block_{block.id}_banner_url', '').strip()
                        if banner_url_val:
                            block.content['banner_url'] = banner_url_val
                        elif event.image:
                            block.content['banner_url'] = event.image.url
                    elif block.block_type == 'concept':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        block.content['subtitle'] = request.POST.get(f'block_{block.id}_subtitle', block.content.get('subtitle', ''))
                        block.content['text_1'] = request.POST.get(f'block_{block.id}_text_1', block.content.get('text_1', ''))
                        block.content['text_2'] = request.POST.get(f'block_{block.id}_text_2', block.content.get('text_2', ''))
                    elif block.block_type == 'audience':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        block.content['subtitle'] = request.POST.get(f'block_{block.id}_subtitle', block.content.get('subtitle', ''))
                        nums = request.POST.getlist(f'block_{block.id}_card_num')
                        titles = request.POST.getlist(f'block_{block.id}_card_title')
                        descs = request.POST.getlist(f'block_{block.id}_card_desc')
                        cards = [{'num': n, 'title': t, 'desc': d} for n, t, d in zip(nums, titles, descs) if t.strip()]
                        if cards:
                            block.content['cards'] = cards
                    elif block.block_type == 'topics':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        block.content['subtitle'] = request.POST.get(f'block_{block.id}_subtitle', block.content.get('subtitle', ''))
                        nums = request.POST.getlist(f'block_{block.id}_topic_num')
                        titles = request.POST.getlist(f'block_{block.id}_topic_title')
                        descs = request.POST.getlist(f'block_{block.id}_topic_desc')
                        topics = [{'num': n, 'title': t, 'desc': d} for n, t, d in zip(nums, titles, descs) if t.strip()]
                        if topics:
                            block.content['topics'] = topics
                    elif block.block_type == 'schedule':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        block.content['subtitle'] = request.POST.get(f'block_{block.id}_subtitle', block.content.get('subtitle', ''))
                        days = request.POST.getlist(f'block_{block.id}_session_day')
                        times = request.POST.getlist(f'block_{block.id}_session_time')
                        titles = request.POST.getlist(f'block_{block.id}_session_title')
                        sessions = [{'day': dy, 'time': tm, 'title': t} for dy, tm, t in zip(days, times, titles) if t.strip()]
                        if sessions:
                            block.content['sessions'] = sessions
                    elif block.block_type == 'speakers':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        block.content['subtitle'] = request.POST.get(f'block_{block.id}_subtitle', block.content.get('subtitle', ''))
                        names = request.POST.getlist(f'block_{block.id}_sp_name')
                        roles = request.POST.getlist(f'block_{block.id}_sp_role')
                        bios = request.POST.getlist(f'block_{block.id}_sp_bio')
                        books = request.POST.getlist(f'block_{block.id}_sp_books')
                        inits = request.POST.getlist(f'block_{block.id}_sp_initials')
                        images = request.POST.getlist(f'block_{block.id}_sp_image')
                        speakers = [{'name': n, 'role': r, 'bio': b, 'books': bk, 'initials': (init or (n[:2].upper() if n else '')), 'image_url': img} for n, r, b, bk, init, img in zip(names, roles, bios, books, inits, images) if n.strip()]
                        if speakers:
                            block.content['speakers'] = speakers
                    elif block.block_type == 'pricing':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        sbp_amt = request.POST.get(f'block_{block.id}_sbp_amount', block.content.get('sbp_amount', ''))
                        sbp_u = request.POST.get(f'block_{block.id}_sbp_url', block.content.get('sbp_url', ''))
                        pp_amt = request.POST.get(f'block_{block.id}_paypal_amount', block.content.get('paypal_amount', ''))
                        pp_u = request.POST.get(f'block_{block.id}_paypal_url', block.content.get('paypal_url', ''))
                        sup_tg = request.POST.get(f'block_{block.id}_support_telegram', block.content.get('support_telegram', ''))
                        block.content['sbp_amount'] = sbp_amt
                        block.content['sbp_url'] = sbp_u
                        block.content['paypal_amount'] = pp_amt
                        block.content['paypal_url'] = pp_u
                        block.content['support_telegram'] = sup_tg
                        if sbp_amt:
                            event.registration_fee = sbp_amt
                        if sbp_u:
                            event.sbp_url = sbp_u
                        if pp_u:
                            event.paypal_url = pp_u
                        if sup_tg:
                            event.support_telegram = sup_tg
                        event.save()
                    elif block.block_type == 'registration':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        block.content['subtitle'] = request.POST.get(f'block_{block.id}_subtitle', block.content.get('subtitle', ''))
                    elif block.block_type == 'faq':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        qs = request.POST.getlist(f'block_{block.id}_faq_q')
                        ans = request.POST.getlist(f'block_{block.id}_faq_a')
                        faq_items = [{'question': q, 'answer': a} for q, a in zip(qs, ans) if q.strip()]
                        if faq_items:
                            block.content['faq_items'] = faq_items
                    elif block.block_type == 'text':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        block.content['lead'] = request.POST.get(f'block_{block.id}_lead', block.content.get('lead', ''))
                        block.content['body'] = request.POST.get(f'block_{block.id}_body', block.content.get('body', ''))
                        block.content['quote'] = request.POST.get(f'block_{block.id}_quote', block.content.get('quote', ''))
                    elif block.block_type == 'custom_html':
                        block.content['title'] = request.POST.get(f'block_{block.id}_title', block.content.get('title', ''))
                        block.content['html'] = request.POST.get(f'block_{block.id}_html', block.content.get('html', ''))
                        block.content['css'] = request.POST.get(f'block_{block.id}_css', block.content.get('css', ''))

                    # Также проверяем, было ли отредактировано поле raw_json (для продвинутых админов)
                    raw_json = request.POST.get(f'block_{block.id}_raw_json', '').strip()
                    if raw_json:
                        try:
                            block.content = json.loads(raw_json)
                        except Exception:
                            pass

                    block.save()

                event.is_conference = True
                event.save()
                messages.success(request, '💾 Все изменения и баннеры лендинга успешно сохранены!')

            return redirect(f'/admin/church_app/event/{event.id}/builder/')

        blocks = event.blocks.all().order_by('order')
        import json
        for b in blocks:
            b.raw_json_str = json.dumps(b.content, ensure_ascii=False, indent=2)

        theme_cfg = event.theme_config or {}
        context = {
            **self.admin_site.each_context(request),
            'event': event,
            'blocks': blocks,
            'block_types': EventBlock.BLOCK_TYPES,
            'theme_config': theme_cfg,
            'title': f'CMS Конструктор: {event.title}',
        }
        return render(request, 'admin/church_app/event/event_builder.html', context)


# ============================================
# EventRegistration Admin
# ============================================
@admin.register(EventRegistration)
class EventRegistrationAdmin(ModelAdmin):
    list_display = ('ticket_number', 'get_participant_name', 'event', 'email', 'phone', 'payment_status', 'registered_at', 'is_confirmed', 'has_receipt')
    list_filter = ('payment_status', 'is_confirmed', 'attended', 'event')
    search_fields = ('ticket_number', 'first_name', 'last_name', 'email', 'phone', 'telegram', 'event__title')
    date_hierarchy = 'registered_at'
    ordering = ('-registered_at',)
    actions = ['confirm_payment_and_registration', 'mark_attended', 'export_as_excel']

    def get_participant_name(self, obj):
        return obj.get_full_name()
    get_participant_name.short_description = "Участник"

    def has_receipt(self, obj):
        if obj.payment_receipt:
            return format_html('<a href="{}" target="_blank" style="color:#27ae60; font-weight:bold;">📄 Чек загружен</a>', obj.payment_receipt.url)
        return format_html('<span style="color:#888;">—</span>')
    has_receipt.short_description = "Чек"

    def confirm_payment_and_registration(self, request, queryset):
        count = queryset.update(payment_status='confirmed', is_confirmed=True)
        self.message_user(request, f"{count} регистраций успешно подтверждено!")

    @admin.action(description="Экспорт в Excel")
    def export_as_excel(self, request, queryset):
        import pandas as pd
        from django.http import HttpResponse
        
        data = []
        for obj in queryset:
            data.append({
                'ID': obj.id,
                'Билет': obj.ticket_number,
                'Имя': obj.first_name,
                'Фамилия': obj.last_name,
                'Событие': obj.event.title if obj.event else '',
                'Email': obj.email,
                'Телефон': obj.phone,
                'Telegram': obj.telegram,
                'Статус оплаты': obj.payment_status,
                'Дата регистрации': obj.registered_at.replace(tzinfo=None) if obj.registered_at else '',
                'Посетил': 'Да' if obj.attended else 'Нет',
                'Подтвержден': 'Да' if obj.is_confirmed else 'Нет',
            })
            
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=registrations.xlsx'
        df.to_excel(response, index=False, engine='openpyxl')
        return response

    confirm_payment_and_registration.short_description = "✓ Подтвердить оплату и участие выбранных"

    def mark_attended(self, request, queryset):
        count = queryset.update(attended=True)
        self.message_user(request, f"Отмечено присутствие для {count} участников!")
    mark_attended.short_description = "Отметить присутствие"


# ============================================
# KidsContent & KidsProgress (Отключены по запросу: детский раздел временно скрыт)
# ============================================
# @admin.register(KidsContent)
# class KidsContentAdmin(ModelAdmin):
#     list_display = ('title', 'content_type', 'age_group', 'views_count', 'is_featured', 'is_active')
#     list_filter = ('content_type', 'age_group', 'is_featured', 'is_active')
#     search_fields = ('title', 'description', 'bible_verse')
#     ordering = ('-is_featured', 'order', '-created_at')
#
# @admin.register(KidsProgress)
# class KidsProgressAdmin(ModelAdmin):
#     list_display = ('user', 'content', 'completed', 'score', 'last_accessed')
#     list_filter = ('completed', 'content__content_type')
#     search_fields = ('user__username', 'content__title')


# ============================================
# DailyVerse Admin
# ============================================
@admin.register(DailyVerse)
class DailyVerseAdmin(ModelAdmin):
    list_display = ('date', 'reference', 'verse_text')
    list_filter = ('date',)
    search_fields = ('verse_text', 'reference')
    ordering = ('-date',)


# ============================================
# PrayerRequest Admin (ОБНОВЛЁННЫЙ)
# ============================================
@admin.register(PrayerRequest)
class PrayerRequestAdmin(ModelAdmin):
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
class PushSubscriptionAdmin(ModelAdmin):
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
class DonationAdmin(ModelAdmin):
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
class NewsAdmin(ModelAdmin):
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
class PastorPhotoAdmin(ModelAdmin):
    list_display = ('slug', 'updated_at')
    search_fields = ('slug',)


# ============================================
# HomeGroup Admin
# ============================================
@admin.register(HomeGroup)
class HomeGroupAdmin(ModelAdmin):
    list_display = ('district', 'address', 'leader_name', 'get_type_display', 'get_day_display', 'time', 'get_age_display', 'is_active', 'order')
    list_filter = ('district', 'group_type', 'day', 'is_active')
    search_fields = ('district', 'address', 'leader_name', 'leader_phone', 'leader_telegram')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'district')
    fieldsets = (
        ('Основная информация', {
            'fields': ('district', 'address', 'group_type', 'description', 'is_active', 'order')
        }),
        ('Лидер и контакты', {
            'fields': ('leader_name', 'leader_phone', 'leader_telegram')
        }),
        ('Геолокация (для интерактивной карты)', {
            'fields': ('latitude', 'longitude'),
            'description': 'Координаты для отображения на карте общины (например: 56.0153, 92.8932)'
        }),
        ('Время проведения', {
            'fields': ('day', 'time')
        }),
        ('Возраст', {
            'fields': ('age_min', 'age_max', 'age_display')
        }),
    )


# ============================================
# UserProfile Admin
# ============================================
@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ('user', 'phone', 'telegram', 'vk', 'city', 'home_group', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'telegram', 'vk', 'phone')


# ============================================
# FavoriteVerse Admin
# ============================================
@admin.register(FavoriteVerse)
class FavoriteVerseAdmin(ModelAdmin):
    list_display = ('user', 'reference', 'created_at')
    search_fields = ('user__username', 'reference', 'verse_text')
    ordering = ('-created_at',)


# ============================================
# PrayerConnection Admin
# ============================================
@admin.register(PrayerConnection)
class PrayerConnectionAdmin(ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')
    ordering = ('-created_at',)


# ============================================
# Revelation & RevelationReaction Admin
# ============================================
@admin.register(Revelation)
class RevelationAdmin(ModelAdmin):
    list_display = ('title', 'user', 'is_public', 'is_anonymous', 'created_at')
    list_filter = ('is_public', 'is_anonymous', 'created_at')
    search_fields = ('title', 'content', 'user__username')
    ordering = ('-created_at',)


@admin.register(RevelationReaction)
class RevelationReactionAdmin(ModelAdmin):
    list_display = ('revelation', 'user', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')


# ============================================
# Ministry & MinistryApplication Admin («Хочу служить»)
# ============================================
@admin.register(Ministry)
class MinistryAdmin(ModelAdmin):
    list_display = ('title', 'category', 'leader_name', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'short_description', 'description', 'leader_name')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'category', 'badge', 'icon', 'is_active', 'order')
        }),
        ('Описания и задачи', {
            'fields': ('short_description', 'description', 'requirements', 'schedule_info')
        }),
        ('Лидер и контакты', {
            'fields': ('leader_name', 'leader_contact')
        }),
        ('Оформление', {
            'fields': ('image', 'gradient_css'),
            'description': 'Баннер служения или CSS-градиент'
        }),
    )


@admin.register(MinistryApplication)
class MinistryApplicationAdmin(ModelAdmin):
    list_display = ('name', 'ministry', 'phone', 'telegram', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('ministry', 'status', 'created_at')
    search_fields = ('name', 'phone', 'telegram', 'email', 'message', 'admin_notes')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Заявка прихожанина', {
            'fields': ('ministry', 'user', 'name', 'phone', 'telegram', 'email', 'message', 'created_at')
        }),
        ('Обработка пастором/лидером', {
            'fields': ('status', 'admin_notes')
        }),
    )