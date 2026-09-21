from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Announcement(models.Model):
    """Главное уведомление на весь экран"""
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(upload_to='announcements/', verbose_name="Изображение")
    button_text = models.CharField(max_length=100, default="Узнать больше", verbose_name="Текст кнопки")
    button_link = models.CharField(max_length=500, default="/news/", verbose_name="Ссылка")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Истекает")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"

class HeroBackground(models.Model):
    """Фон для главной страницы (Слайдер)"""
    title = models.CharField(max_length=150, blank=True, verbose_name="Название (для админки)")
    image = models.ImageField(upload_to='hero_backgrounds/', blank=True, null=True, verbose_name="Изображение / Постер")
    video_url = models.CharField(max_length=500, blank=True, verbose_name="Ссылка на MP4-видео", help_text="Например: https://kclc.ru/wp-content/uploads/2024/09/фон-на-сайт.mp4")
    link_url = models.CharField(max_length=500, blank=True, verbose_name="Ссылка при клике (кнопка)", help_text="Например: /events/onlajn-zvuki-nebes/ или https://...")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Фон главной страницы"
        verbose_name_plural = "Фоны главной страницы"

    def __str__(self):
        return self.title or f"Фон #{self.id}"

class Category(models.Model):
    """Категория контента в библиотеке"""
    CATEGORY_TYPES = [
        ('video', 'Видео'),
        ('bible', 'Чтение Библии'),
        ('events', 'События'),
        ('calendar', 'Календарь'),
        ('kids', 'Детский раздел'),
    ]

    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="URL")
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, verbose_name="Тип")
    icon = models.CharField(max_length=50, default='fa-folder', verbose_name="Иконка FontAwesome")
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Изображение")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Video(models.Model):
    """Видео материалы"""
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos', limit_choices_to={'category_type': 'video'})
    video_file = models.FileField(upload_to='videos/', blank=True, null=True, verbose_name="Видео файл")
    youtube_url = models.URLField(blank=True, null=True, verbose_name="YouTube ссылка")
    rutube_url = models.URLField(blank=True, null=True, verbose_name="Rutube ссылка")
    vk_url = models.URLField(blank=True, null=True, verbose_name="VK Video ссылка")
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True, verbose_name="Превью")
    duration = models.IntegerField(default=0, help_text="Длительность в секундах", verbose_name="Длительность")
    views_count = models.IntegerField(default=0, verbose_name="Просмотры")
    published_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="Дата публикации")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемое")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = "Видео"
        verbose_name_plural = "Видео"

    def __str__(self):
        return self.title

    def get_effective_date(self):
        """Returns published_at if available, otherwise created_at"""
        return self.published_at or self.created_at

    def get_views_display(self):
        """Returns formatted view count, e.g. 1.5K or 820"""
        count = self.views_count
        if count >= 1000000:
            return f"{count / 1000000:.1f}M".replace('.0', '')
        if count >= 1000:
            return f"{count / 1000:.1f}K".replace('.0', '')
        return str(count)

    def get_video_url(self):
        if self.video_file:
            return self.video_file.url
        return self.youtube_url or self.rutube_url

    def get_youtube_id(self):
        """Extracts 11-char YouTube video ID"""
        import re
        if not self.youtube_url:
            return None
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})', self.youtube_url)
        return match.group(1) if match else None

    def get_youtube_embed_url(self):
        """Converts any YouTube URL format to privacy-enhanced embed URL (resolves error 153)"""
        yt_id = self.get_youtube_id()
        if yt_id:
            return f'https://www.youtube-nocookie.com/embed/{yt_id}?enablejsapi=1&rel=0&modestbranding=1'
        return None

    def get_rutube_embed_url(self):
        """Converts Rutube video URL to embed URL"""
        import re
        if not self.rutube_url:
            return None
        match = re.search(r'rutube\.ru/(?:video|play/embed)/([a-zA-Z0-9_-]+)', self.rutube_url)
        if match:
            return f'https://rutube.ru/play/embed/{match.group(1)}'
        return None

    def get_vk_embed_url(self):
        """Converts VK video URL to embed URL"""
        import re
        if not self.vk_url:
            return None
        if 'video_ext.php' in self.vk_url:
            return self.vk_url
        match = re.search(r'video(-?\d+)_(\d+)', self.vk_url)
        if match:
            oid, vid = match.group(1), match.group(2)
            return f'https://vk.com/video_ext.php?oid={oid}&id={vid}&hd=2'
        return None

    def get_duration_display(self):
        """Returns duration in human-readable format (MM:SS or Xч YYмин)"""
        if not self.duration:
            return ''
        total = int(self.duration)
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        if hours > 0:
            return f'{hours}ч {minutes:02d}мин'
        elif minutes > 0:
            return f'{minutes}:{seconds:02d}'
        else:
            return f'0:{seconds:02d}'

    def get_duration_minutes(self):
        """Returns duration in minutes (rounded)"""
        if not self.duration:
            return 0
        return max(1, round(self.duration / 60))

    def increment_views(self):
        self.views_count += 1


class PodcastEpisode(models.Model):
    """Локальный каталог выпусков подкаста."""
    title = models.CharField(max_length=300, verbose_name="Название")
    speaker = models.CharField(max_length=200, blank=True, verbose_name="Спикер")
    duration = models.CharField(max_length=20, blank=True, verbose_name="Длительность")
    episode_url = models.URLField(max_length=500, blank=True, verbose_name="Ссылка на выпуск")
    audio_url = models.URLField(max_length=1000, blank=True, verbose_name="Аудио")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Выпуск подкаста"
        verbose_name_plural = "Выпуски подкаста"

    def __str__(self):
        return self.title

class BiblePlan(models.Model):
    """Планы чтения Библии"""
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(upload_to='bible_plans/', blank=True, null=True, verbose_name="Изображение")
    days_count = models.IntegerField(default=7, verbose_name="Количество дней")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "План чтения"
        verbose_name_plural = "Планы чтения"

    def __str__(self):
        return self.title

class BibleReading(models.Model):
    """День чтения в плане"""
    plan = models.ForeignKey(BiblePlan, on_delete=models.CASCADE, related_name='readings')
    day_number = models.IntegerField(verbose_name="День")
    title = models.CharField(max_length=200, verbose_name="Название")
    bible_passage = models.CharField(max_length=200, verbose_name="Отрывок (например: Иоанна 3:16)")
    start_chapter = models.CharField(max_length=50, verbose_name="Начало", help_text="Книга Глава:Стих")
    end_chapter = models.CharField(max_length=50, blank=True, null=True, verbose_name="Конец")
    content = models.TextField(blank=True, verbose_name="Дополнительный текст")

    class Meta:
        ordering = ['plan', 'day_number']
        unique_together = ['plan', 'day_number']
        verbose_name = "День чтения"
        verbose_name_plural = "Дни чтения"

    def __str__(self):
        return f"{self.plan.title} - День {self.day_number}: {self.title}"

class UserBibleProgress(models.Model):
    """Прогресс пользователя в чтении Библии"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bible_progress')
    plan = models.ForeignKey(BiblePlan, on_delete=models.CASCADE)
    current_day = models.IntegerField(default=0)
    completed_days = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_read_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'plan']
        verbose_name = "Прогресс чтения"
        verbose_name_plural = "Прогресс чтения"

    def __str__(self):
        return f"{self.user.username} - {self.plan.title} ({self.current_day}/{self.plan.days_count})"

    def mark_day_completed(self, day_number):
        if day_number not in self.completed_days:
            self.completed_days.append(day_number)
            if day_number > self.current_day:
                self.current_day = day_number
            self.completed_days = list(self.completed_days)
            self.save()

    def get_progress_percentage(self):
        if self.plan and self.plan.days_count > 0:
            return int((len(self.completed_days) / self.plan.days_count) * 100)
        return 0

class Event(models.Model):
    """События"""
    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True, verbose_name="URL")
    description = models.TextField(verbose_name="Описание")
    event_type = models.CharField(max_length=50, choices=[
        ('service', 'Богослужение'),
        ('youth', 'Молодежка'),
        ('kids', 'Детское служение'),
        ('study', 'Библейский урок'),
        ('prayer', 'Молитвенное собрание'),
        ('special', 'Особое событие'),
    ], default='service', verbose_name="Тип события")
    start_date = models.DateTimeField(verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    location = models.CharField(max_length=200, verbose_name="Место проведения")
    address = models.TextField(blank=True, verbose_name="Адрес")
    image = models.ImageField(upload_to='events/', blank=True, null=True, verbose_name="Изображение")
    max_participants = models.IntegerField(default=0, help_text="0 = без ограничений", verbose_name="Макс. участников")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемое")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']
        verbose_name = "Событие"
        verbose_name_plural = "События"

    def __str__(self):
        return f"{self.title} - {self.start_date.strftime('%d.%m.%Y')}"

    def is_past(self):
        return self.end_date < timezone.now()

    def days_until(self):
        if self.start_date > timezone.now():
            return (self.start_date - timezone.now()).days
        return 0

    is_conference = models.BooleanField(default=False, verbose_name="Является конференцией/лендингом")
    theme_config = models.JSONField(default=dict, blank=True, verbose_name="Настройки темы и оформления визитки")
    registration_fee = models.CharField(max_length=150, blank=True, verbose_name="Регистрационное пожертвование (текст)")
    sbp_url = models.URLField(blank=True, verbose_name="Ссылка на пожертвование по СБП")
    paypal_url = models.URLField(blank=True, verbose_name="Ссылка на PayPal")
    support_telegram = models.CharField(max_length=100, blank=True, default='@krasnkate', verbose_name="Telegram куратора/поддержки")
    stream_link = models.URLField(blank=True, verbose_name="Ссылка на трансляцию/материалы для участников")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Широта для карты")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Долгота для карты")
    is_online = models.BooleanField(default=False, verbose_name="Онлайн формат")

    def save(self, *args, **kwargs):
        if not self.slug:
            translit_map = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
                'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
                'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
                'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
                'я': 'ya'
            }
            s = (self.title or '').lower()
            translit_str = ''.join(translit_map.get(c, c) for c in s)
            from django.utils.text import slugify
            base_slug = slugify(translit_str)
            if not base_slug:
                base_slug = f"event-{self.id or uuid.uuid4().hex[:6]}"
            candidate = base_slug[:180]
            slug = candidate
            idx = 1
            while Event.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{candidate}-{idx}"
                idx += 1
            self.slug = slug
        super().save(*args, **kwargs)


class EventBlock(models.Model):
    """Блоки конструктора страниц для сложных лендингов (конференций)"""
    BLOCK_TYPES = [
        ('hero', 'Главный экран (Hero) и баннер'),
        ('concept', 'Концепция / Манифест'),
        ('audience', 'Для кого эта школа / событие'),
        ('topics', 'Темы и модули обучения'),
        ('schedule', 'Расписание и формат'),
        ('speakers', 'Спикеры конференции'),
        ('pricing', 'Пожертвование и реквизиты'),
        ('registration', 'Форма регистрации'),
        ('faq', 'Часто задаваемые вопросы (FAQ)'),
        ('video', 'Видео / Трейлер'),
        ('reviews', 'Отзывы участников'),
        ('custom_html', 'Кастомный HTML / Код от ИИ'),
        ('text', 'Произвольный текстовый блок'),
        ('image_gallery', 'Галерея изображений'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='blocks', verbose_name="Событие")
    block_type = models.CharField(max_length=50, choices=BLOCK_TYPES, verbose_name="Тип блока")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок вывода")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    # JSONField allows us to store arbitrary data based on block_type without changing DB schema
    content = models.JSONField(default=dict, blank=True, help_text="Данные блока (заполняется через CMS конструктор)", verbose_name="Контент блока")
    
    class Meta:
        ordering = ['order']
        verbose_name = "Блок лендинга"
        verbose_name_plural = "Блоки лендингов"

    def __str__(self):
        return f"{self.get_block_type_display()} ({self.order}) - {self.event.title}"


class EventRegistration(models.Model):
    """Регистрация на события и конференции"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'На проверке чека'),
        ('confirmed', 'Подтверждено'),
        ('free', 'Бесплатное участие'),
        ('rejected', 'Отклонено'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations', verbose_name="Событие")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='event_registrations', verbose_name="Пользователь")
    
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Фамилия")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Телефон")
    telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram")
    
    payment_receipt = models.FileField(upload_to='event_receipts/%Y/%m/', null=True, blank=True, verbose_name="Чек об оплате/пожертвовании")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Статус оплаты")
    ticket_number = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Номер билета")
    notes = models.TextField(blank=True, verbose_name="Заметки администратора")
    
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    is_confirmed = models.BooleanField(default=False, verbose_name="Регистрация подтверждена")
    attended = models.BooleanField(default=False, verbose_name="Присутствовал")

    class Meta:
        ordering = ['-registered_at']
        verbose_name = "Регистрация на событие"
        verbose_name_plural = "Регистрации на события"

    def __str__(self):
        name = self.get_full_name() or (self.user.username if self.user else 'Гость')
        return f"{self.ticket_number or 'Без номера'} — {name} ({self.event.title})"

    def get_full_name(self):
        parts = [p for p in [self.first_name, self.last_name] if p]
        if parts:
            return " ".join(parts)
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.email or "Участник"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            import random
            import string
            prefix = "KCLC"
            rand_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.ticket_number = f"{prefix}-{self.event.id}-{rand_code}"
        super().save(*args, **kwargs)

class KidsContent(models.Model):
    """Детский контент"""
    CONTENT_TYPES = [
        ('cartoon', 'Мультфильм'),
        ('lesson', 'Урок'),
        ('game', 'Игра'),
        ('craft', 'Поделка'),
        ('song', 'Песня'),
    ]
    AGE_GROUPS = [
        ('3-5', '3-5 лет'),
        ('6-8', '6-8 лет'),
        ('9-12', '9-12 лет'),
        ('all', 'Все возрасты'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, verbose_name="Тип контента")
    age_group = models.CharField(max_length=10, choices=AGE_GROUPS, default='all', verbose_name="Возрастная группа")
    video_file = models.FileField(upload_to='kids_videos/', blank=True, null=True, verbose_name="Видео файл")
    youtube_url = models.URLField(blank=True, null=True, verbose_name="YouTube ссылка")
    rutube_url = models.URLField(blank=True, null=True, verbose_name="Rutube ссылка")
    vk_url = models.URLField(blank=True, null=True, verbose_name="VK Video ссылка")
    thumbnail = models.ImageField(upload_to='kids_thumbnails/', blank=True, null=True, verbose_name="Превью")
    bible_verse = models.CharField(max_length=200, blank=True, verbose_name="Библейский стих")
    game_data = models.JSONField(default=dict, blank=True, verbose_name="Данные игры")
    printable_material = models.FileField(upload_to='kids_printables/', blank=True, null=True, verbose_name="Материал для печати")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемое")
    views_count = models.IntegerField(default=0, verbose_name="Просмотры")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']
        verbose_name = "Детский контент"
        verbose_name_plural = "Детский контент"

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title}"

    def get_youtube_embed_url(self):
        import re
        if not self.youtube_url:
            return None
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, self.youtube_url)
            if match:
                return f'https://www.youtube-nocookie.com/embed/{match.group(1)}?enablejsapi=1&rel=0&modestbranding=1'
        return None

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

class KidsProgress(models.Model):
    """Прогресс ребенка"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kids_progress')
    content = models.ForeignKey(KidsContent, on_delete=models.CASCADE, related_name='progress')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0, help_text="Для игр - очки", verbose_name="Результат")
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'content']
        verbose_name = "Прогресс ребенка"
        verbose_name_plural = "Прогресс детей"

    def __str__(self):
        return f"{self.user.username} - {self.content.title}"

class DailyVerse(models.Model):
    """Стих дня на главной странице"""
    verse_text = models.TextField(verbose_name="Текст стиха")
    reference = models.CharField(max_length=100, verbose_name="Ссылка (напр. Иоанна 3:16)")
    date = models.DateField(unique=True, verbose_name="Дата")
    reflection = models.TextField(blank=True, null=True, verbose_name="Короткое размышление")

    class Meta:
        verbose_name = "Стих дня"
        verbose_name_plural = "Стихи дня"

    def __str__(self):
        return f"{self.date} - {self.reference}"

    @classmethod
    def get_today_verse(cls):
        from django.utils import timezone
        today = timezone.localdate()
        verse = cls.objects.filter(date=today).first()
        if verse:
            return verse
        try:
            from .daily_verse_data import VERSES
            day_of_year = today.toordinal()
            verse_index = day_of_year % len(VERSES)
            verse_data = VERSES[verse_index]
            
            class MockVerse:
                def __init__(self, text, reference):
                    self.verse_text = text
                    self.reference = reference
                    self.reflection = ""
            return MockVerse(verse_data['text'], verse_data['ref'])
        except Exception:
            return cls.objects.order_by('-date').first()

class PrayerRequestManager(models.Manager):
    """Менеджер для фильтрации молитвенных нужд"""
    def active(self):
        """Только активные (не отвеченные) молитвы"""
        return self.filter(is_answered=False)
    
    def answered(self):
        """Только отвеченные молитвы"""
        return self.filter(is_answered=True)

class PrayerRequest(models.Model):
    """Молитвенная нужда"""
    PRAYER_CATEGORIES = [
        ('general', 'Общая нужда'),
        ('health', 'Здоровье и исцеление'),
        ('family', 'Семья и дети'),
        ('spiritual', 'Духовная жизнь'),
        ('finance', 'Работа и финансы'),
        ('thanks', 'Благодарность Богу'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Тема молитвы")
    description = models.TextField(verbose_name="Описание нужды")
    category = models.CharField(max_length=30, choices=PRAYER_CATEGORIES, default='general', verbose_name="Категория")
    is_answered = models.BooleanField(default=False, verbose_name="Получен ответ")
    prayer_count = models.IntegerField(default=0, verbose_name="Сколько человек молится")
    is_public = models.BooleanField(default=True, verbose_name="Публичная просьба")
    is_anonymous = models.BooleanField(default=False, verbose_name="Анонимная просьба")
    supporters = models.ManyToManyField(User, related_name='supported_prayers', blank=True, verbose_name="Кто поддержал в молитве")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата ответа")
    
    # Используем кастомный менеджер
    objects = PrayerRequestManager()

    class Meta:
        verbose_name = "Молитвенная нужда"
        verbose_name_plural = "Молитвенные нужды"

    def __str__(self):
        return f"{self.title} - {self.get_author_display()}"

    def get_author_display(self):
        if self.is_anonymous:
            return "Анонимная просьба"
        return self.user.username

class PushSubscription(models.Model):
    """Подписка на Web Push уведомления"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions', null=True, blank=True, verbose_name="Пользователь")
    endpoint = models.URLField(max_length=500, unique=True, verbose_name="Endpoint")
    p256dh = models.CharField(max_length=100, verbose_name="Ключ p256dh")
    auth = models.CharField(max_length=100, verbose_name="Ключ auth")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подписки")

    class Meta:
        verbose_name = "Push Подписка"
        verbose_name_plural = "Push Подписки"

    def __str__(self):
        username = self.user.username if self.user else "Аноним"
        return f"Подписка ({username})"

class Donation(models.Model):
    """Пожертвования"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="ID платежа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Пожертвование"
        verbose_name_plural = "Пожертвования"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.amount} ₽ - {self.get_status_display()}"

class News(models.Model):
    """Новости для главной страницы"""
    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок"
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="URL"
    )
    short_description = models.TextField(
        verbose_name="Краткое описание"
    )
    content = models.TextField(
        verbose_name="Полный текст"
    )
    image = models.ImageField(
        upload_to='news/',
        blank=True,
        null=True,
        verbose_name="Изображение"
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Главная новость"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Опубликовано"
    )
    views_count = models.IntegerField(
        default=0,
        verbose_name="Просмотры"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата публикации (опционально, заменяет дату создания)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-is_featured', '-published_at', '-created_at']
        verbose_name = "Новость"
        verbose_name_plural = "Новости"

    def __str__(self):
        return self.title

class PastorPhoto(models.Model):
    slug = models.SlugField(unique=True, verbose_name="Идентификатор пастора")
    image = models.ImageField(upload_to='pastors/', verbose_name="Фото", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Фото пастора"
        verbose_name_plural = "Фото пасторов"

    def __str__(self):
        return self.slug

class HomeGroup(models.Model):
    """Домашняя группа / встреча"""
    DAYS_OF_WEEK = [
        ('monday', 'Понедельник'),
        ('tuesday', 'Вторник'),
        ('wednesday', 'Среда'),
        ('thursday', 'Четверг'),
        ('friday', 'Пятница'),
        ('saturday', 'Суббота'),
        ('sunday', 'Воскресенье'),
        ('negotiable', 'По договоренности'),
    ]
    GROUP_TYPES = [
        ('mixed', 'Смешанная'),
        ('male', 'Мужская'),
        ('female', 'Женская'),
        ('youth', 'Молодежная'),
        ('teen', 'Подростковая'),
    ]

    district = models.CharField(max_length=100, verbose_name="Район")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES, default='mixed', verbose_name="Тип группы")
    day = models.CharField(max_length=20, choices=DAYS_OF_WEEK, default='negotiable', verbose_name="День недели")
    time = models.CharField(max_length=20, blank=True, null=True, verbose_name="Время (например: 19:00)")
    age_min = models.IntegerField(default=0, blank=True, null=True, verbose_name="Минимальный возраст")
    age_max = models.IntegerField(default=0, blank=True, null=True, verbose_name="Максимальный возраст")
    age_display = models.CharField(max_length=50, blank=True, null=True, verbose_name="Возраст (текстом, если диапазон)")
    leader_name = models.CharField(max_length=150, blank=True, verbose_name="Лидер группы")
    leader_phone = models.CharField(max_length=50, blank=True, verbose_name="Телефон лидера")
    leader_telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram лидера")
    description = models.TextField(blank=True, verbose_name="Описание группы")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Широта (Latitude)")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Долгота (Longitude)")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'district', 'day']
        verbose_name = "Домашняя группа"
        verbose_name_plural = "Домашние группы"

    def __str__(self):
        return f"{self.district} - {self.address}"

    def get_age_display(self):
        if self.age_display:
            return self.age_display
        if self.age_min and self.age_max:
            if self.age_min == self.age_max:
                return f"{self.age_min} лет"
            return f"{self.age_min}-{self.age_max} лет"
        if self.age_min:
            return f"от {self.age_min} лет"
        if self.age_max:
            return f"до {self.age_max} лет"
        return "Все возрасты"

    def get_day_display(self):
        return dict(self.DAYS_OF_WEEK).get(self.day, self.day)

    def get_type_display(self):
        return dict(self.GROUP_TYPES).get(self.group_type, self.group_type)


class EmailVerificationOTP(models.Model):
    """Одноразовый 6-значный код подтверждения email"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_otps', verbose_name="Пользователь")
    email = models.EmailField(verbose_name="Email")
    code = models.CharField(max_length=6, verbose_name="6-значный код")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    expires_at = models.DateTimeField(verbose_name="Истекает")
    is_used = models.BooleanField(default=False, verbose_name="Использован")
    attempts = models.IntegerField(default=0, verbose_name="Попыток ввода")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "OTP код подтверждения"
        verbose_name_plural = "OTP коды подтверждения"

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at and self.attempts < 5

    def __str__(self):
        return f"{self.user.username} - {self.code} ({self.email})"
class Revelation(models.Model):
    """Откровения и свидетельства"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Тема/Заголовок")
    content = models.TextField(verbose_name="Текст откровения/свидетельства")
    is_public = models.BooleanField(default=True, verbose_name="Публичное")
    is_anonymous = models.BooleanField(default=False, verbose_name="Анонимное")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    
    class Meta:
        verbose_name = "Откровение/Свидетельство"
        verbose_name_plural = "Откровения и свидетельства"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_author_display()}"

    def get_author_display(self):
        if self.is_anonymous:
            return "Анонимное свидетельство"
        return self.user.username

class RevelationReaction(models.Model):
    """Реакции на откровения"""
    REACTION_CHOICES = [
        ('amen', '🙏 Аминь'),
        ('glory', '❤️ Слава Богу'),
        ('fire', '🔥 Вдохновляет'),
        ('grace', '🕊️ Благодать'),
    ]
    revelation = models.ForeignKey(Revelation, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['revelation', 'user', 'reaction_type']
        verbose_name = "Реакция"
        verbose_name_plural = "Реакции"

    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_type_display()} on {self.revelation.title}"


class UserProfile(models.Model):
    """Расширенный профиль пользователя церкви KCLC"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Номер телефона")
    telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram (@username или ссылка)")
    vk = models.CharField(max_length=100, blank=True, verbose_name="ВКонтакте (ссылка или id/username)")
    city = models.CharField(max_length=100, blank=True, verbose_name="Город / Район")
    bio = models.TextField(max_length=500, blank=True, verbose_name="О себе / Свидетельство")
    home_group = models.CharField(max_length=150, blank=True, verbose_name="Домашняя группа")
    baptism_date = models.DateField(null=True, blank=True, verbose_name="Дата крещения / духовный день рождения")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватар")
    avatar_color = models.CharField(max_length=50, default="from-amber-400 to-amber-600", verbose_name="Цвет аватара")
    is_public = models.BooleanField(default=True, verbose_name="Открытый профиль для прихожан")
    notify_daily_verse = models.BooleanField(default=True, verbose_name="Стих дня каждое утро")
    notify_prayer_answers = models.BooleanField(default=True, verbose_name="Ответы на молитвы")
    notify_events = models.BooleanField(default=True, verbose_name="Церковные события")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль {self.user.username}"

    def get_display_name(self):
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full if full else self.user.username

    def get_initials(self):
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        if self.user.first_name:
            return self.user.first_name[:2].upper()
        return self.user.username[:2].upper()

    def get_avatar_url(self):
        """Возвращает URL аватара или None, если фото не загружено"""
        if self.avatar and hasattr(self.avatar, 'url'):
            try:
                return self.avatar.url
            except Exception:
                return None
        return None

    def get_telegram_url(self):
        if not self.telegram:
            return ""
        val = self.telegram.strip()
        if val.startswith("https://t.me/") or val.startswith("http://t.me/"):
            return val
        if val.startswith("@"):
            return f"https://t.me/{val[1:]}"
        return f"https://t.me/{val}"

    def get_vk_url(self):
        if not self.vk:
            return ""
        val = self.vk.strip()
        if val.startswith("http://") or val.startswith("https://"):
            return val
        return f"https://vk.com/{val}"

    def get_days_in_church(self):
        delta = timezone.now().date() - self.user.date_joined.date()
        return max(1, delta.days)


class FavoriteVerse(models.Model):
    """Любимые стихи из Библии у пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_verses', verbose_name="Пользователь")
    reference = models.CharField(max_length=150, verbose_name="Место Писания (напр. Иоанна 3:16)")
    verse_text = models.TextField(verbose_name="Текст стиха")
    note = models.CharField(max_length=255, blank=True, verbose_name="Личная заметка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлен")

    class Meta:
        verbose_name = "Любимый стих"
        verbose_name_plural = "Любимые стихи"
        ordering = ['-created_at']
        unique_together = ['user', 'reference']

    def __str__(self):
        return f"{self.user.username} - {self.reference}"


class PrayerConnection(models.Model):
    """Молитвенная связь / Молитвенные друзья"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prayer_following', verbose_name="Кто молится")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prayer_followers', verbose_name="За кого молится")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Связаны с")

    class Meta:
        verbose_name = "Молитвенная связь"
        verbose_name_plural = "Молитвенные связи"
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.username} молится за {self.to_user.username}"

    def is_mutual(self):
        return PrayerConnection.objects.filter(from_user=self.to_user, to_user=self.from_user).exists()


class Ministry(models.Model):
    """Служение церкви («Хочу служить» / Команды церкви)"""
    CATEGORY_CHOICES = [
        ('media', 'Медиа и Креатив'),
        ('worship', 'Музыка и Прославление'),
        ('hospitality', 'Гостеприимство и Порядок'),
        ('nextgen', 'Дети и Молодёжь'),
        ('care', 'Забота и Молитва'),
        ('social', 'Социальное служение'),
        ('admin', 'Организация и ивенты'),
    ]

    title = models.CharField(max_length=150, verbose_name="Название служения")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL slug")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='media', verbose_name="Категория служения")
    icon = models.CharField(max_length=50, default='volunteer_activism', verbose_name="Иконка (Material Symbols)")
    badge = models.CharField(max_length=60, blank=True, verbose_name="Бейдж/направление")
    short_description = models.CharField(max_length=300, verbose_name="Краткое описание")
    description = models.TextField(verbose_name="Подробное описание и задачи")
    requirements = models.TextField(blank=True, verbose_name="Требования к волонтёру")
    schedule_info = models.CharField(max_length=200, blank=True, verbose_name="Время и график служения")
    leader_name = models.CharField(max_length=150, blank=True, verbose_name="Лидер служения")
    leader_contact = models.CharField(max_length=100, blank=True, verbose_name="Telegram / телефон лидера")
    image = models.ImageField(upload_to='ministries/', blank=True, null=True, verbose_name="Баннер / фото служения")
    gradient_css = models.CharField(max_length=255, default='from-blue-600/30 to-indigo-900/40', verbose_name="CSS градиент для фона")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Служение"
        verbose_name_plural = "Служения"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('ministry_detail', kwargs={'slug': self.slug})


class MinistryApplication(models.Model):
    """Заявка на служение от прихожанина («Хочу служить»)"""
    STATUS_CHOICES = [
        ('new', 'Новая заявка'),
        ('contacted', 'Связались'),
        ('accepted', 'Принят в команду'),
        ('declined', 'Отклонена'),
    ]

    ministry = models.ForeignKey(Ministry, on_delete=models.CASCADE, related_name='applications', verbose_name="Служение")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ministry_applications', verbose_name="Пользователь")
    name = models.CharField(max_length=150, verbose_name="Имя и фамилия")
    phone = models.CharField(max_length=50, verbose_name="Номер телефона")
    telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram")
    email = models.EmailField(blank=True, verbose_name="Email")
    message = models.TextField(blank=True, verbose_name="Опыт, таланты или пожелания")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус заявки")
    admin_notes = models.TextField(blank=True, verbose_name="Заметки служителя / пастора")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подачи")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Заявка на служение"
        verbose_name_plural = "Заявки на служение"

    def __str__(self):
        return f"{self.name} -> {self.ministry.title} ({self.get_status_display()})"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

