from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SpiritualLevel(models.Model):
    """Уровень на духовном пути - здание в городе"""
    LEVEL_TYPES = [
        ('basic', 'Основы веры'),
        ('growth', 'Духовный рост'),
        ('service', 'Служение'),
        ('leadership', 'Лидерство'),
        ('worship', 'Поклонение'),
        ('prayer', 'Молитва'),
        ('study', 'Изучение'),
        ('fellowship', 'Общение'),
    ]
    
    BUILDING_STYLES = [
        ('church', 'Церковь'),
        ('chapel', 'Часовня'),
        ('cathedral', 'Собор'),
        ('monastery', 'Монастырь'),
        ('temple', 'Храм'),
        ('house', 'Дом'),
        ('library', 'Библиотека'),
        ('school', 'Школа'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название уровня")
    description = models.TextField(verbose_name="Описание")
    level_type = models.CharField(max_length=50, choices=LEVEL_TYPES, default='basic')
    building_style = models.CharField(max_length=50, choices=BUILDING_STYLES, default='church')
    order = models.IntegerField(verbose_name="Порядковый номер")
    image = models.ImageField(upload_to='levels/', blank=True, null=True, verbose_name="Изображение")
    is_available = models.BooleanField(default=True, verbose_name="Доступен")
    position_x = models.IntegerField(default=0, verbose_name="Позиция X")
    position_y = models.IntegerField(default=0, verbose_name="Позиция Y")
    height = models.IntegerField(default=3, verbose_name="Высота здания")
    color = models.CharField(max_length=20, default='#3498db', verbose_name="Цвет здания")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.order}. {self.title}"
    
    class Meta:
        ordering = ['order']
        verbose_name = "Уровень духовного пути"
        verbose_name_plural = "Уровни духовного пути"


class UserProgress(models.Model):
    """Прогресс пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    level = models.ForeignKey(SpiritualLevel, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False, verbose_name="Пройден")
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.IntegerField(default=0, verbose_name="Процент выполнения")
    
    class Meta:
        unique_together = ['user', 'level']
        verbose_name = "Прогресс пользователя"
        verbose_name_plural = "Прогресс пользователей"
    
    def __str__(self):
        return f"{self.user.username} - {self.level.title}"


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


# Модели для библиотеки
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
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True, verbose_name="Превью")
    duration = models.IntegerField(default=0, help_text="Длительность в секундах", verbose_name="Длительность")
    views_count = models.IntegerField(default=0, verbose_name="Просмотры")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемое")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']
        verbose_name = "Видео"
        verbose_name_plural = "Видео"
    
    def __str__(self):
        return self.title
    
    def get_video_url(self):
        if self.video_file:
            return self.video_file.url
        return self.youtube_url
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])


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
    completed_days = models.JSONField(default=list, blank=True)  # Список завершенных дней
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
            self.save()
    
    def get_progress_percentage(self):
        if self.plan and self.plan.days_count > 0:
            return int((len(self.completed_days) / self.plan.days_count) * 100)
        return 0


class Event(models.Model):
    """События"""
    title = models.CharField(max_length=200, verbose_name="Название")
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


class EventRegistration(models.Model):
    """Регистрация на события"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    attended = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['event', 'user']
        verbose_name = "Регистрация"
        verbose_name_plural = "Регистрации"
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


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
    thumbnail = models.ImageField(upload_to='kids_thumbnails/', blank=True, null=True, verbose_name="Превью")
    bible_verse = models.CharField(max_length=200, blank=True, verbose_name="Библейский стих")
    game_data = models.JSONField(default=dict, blank=True, verbose_name="Данные игры")  # Для интерактивных игр
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

class PrayerRequest(models.Model):
    """Молитвенная нужда (Молитвенный трекер)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Тема молитвы")
    description = models.TextField(verbose_name="Описание нужды")
    is_answered = models.BooleanField(default=False, verbose_name="Получен ответ")
    prayer_count = models.IntegerField(default=0, verbose_name="Сколько человек молится")
    is_public = models.BooleanField(default=True, verbose_name="Публичная просьба")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата ответа")

    class Meta:
        verbose_name = "Молитвенная нужда"
        verbose_name_plural = "Молитвенные нужды"

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class ChatRoom(models.Model):
    """Комната чата (группа, форум)"""
    name = models.CharField(max_length=150, verbose_name="Название чата")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    icon = models.CharField(max_length=50, default="forum", verbose_name="Иконка (Material Symbols)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")

    class Meta:
        verbose_name = "Комната чата"
        verbose_name_plural = "Комнаты чатов"

    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    """Сообщение в чате"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name="Чат")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    text = models.TextField(verbose_name="Текст сообщения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")

    class Meta:
        verbose_name = "Сообщение чата"
        verbose_name_plural = "Сообщения чата"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username} ({self.created_at.strftime('%d.%m %H:%M')})"

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