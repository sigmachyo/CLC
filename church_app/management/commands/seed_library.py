import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from church_app.models import Category, Video, Event, KidsContent, DailyVerse

class Command(BaseCommand):
    help = 'Seeds the database with test data for the Library'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing library data...')
        Category.objects.all().delete()
        Video.objects.all().delete()
        Event.objects.all().delete()
        KidsContent.objects.all().delete()
        DailyVerse.objects.all().delete()

        self.stdout.write('Creating Categories...')
        cat_worship = Category.objects.create(name='Прославление', slug='worship', description='Музыка и песни поклонения', icon='fa-video')
        cat_sermons = Category.objects.create(name='Проповеди', slug='sermons', description='Воскресные послания и учения', icon='fa-bible')
        cat_podcasts = Category.objects.create(name='Подкасты', slug='podcasts', description='Беседы на духовные темы', icon='fa-video')
        cat_kids = Category.objects.create(name='Детям', slug='kids', description='Мультики и уроки', icon='fa-child')

        self.stdout.write('Creating Daily Verse...')
        DailyVerse.objects.create(
            date=timezone.now().date(),
            verse_text='Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного, дабы всякий верующий в Него, не погиб, но имел жизнь вечную.',
            reference='Иоанна 3:16',
            reflection='Божья любовь безгранична и безусловна. Поразмышляйте сегодня о том даре, который был дан нам через Христа.'
        )

        self.stdout.write('Creating Videos...')
        videos = [
            ('Сила веры в трудные времена', 'Мощное послание о вере.', cat_sermons),
            ('Прославление - Воскресенье 12.05', 'Запись воскресного поклонения.', cat_worship),
            ('Как молиться?', 'Практические советы о молитве.', cat_podcasts),
            ('История церкви', 'Документальный фильм.', cat_sermons),
            ('Молодежное служение - Влог', 'Как прошло наше собрание.', cat_worship)
        ]
        
        for i, (title, desc, cat) in enumerate(videos):
            Video.objects.create(
                title=title,
                description=desc,
                category=cat,
                # YouTube video ID (some random worship/sermon videos or just placeholders)
                youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ' if i%2==0 else 'https://www.youtube.com/watch?v=jNQXAC9IVRw', 
                duration=random.randint(900, 5400),
                views_count=random.randint(100, 5000)
            )

        self.stdout.write('Creating Events...')
        events = [
            ('Рождественский концерт', 'Празднуем Рождество вместе!', timezone.now() + timedelta(days=10), 'Главный зал'),
            ('Молодежная встреча', 'Общение, игры, слово.', timezone.now() + timedelta(days=2), 'Зал №2'),
            ('Женская конференция', 'Специальное время для сестер.', timezone.now() + timedelta(days=30), 'Главный зал'),
            ('Библейская школа', 'Изучаем послание к Римлянам.', timezone.now() + timedelta(days=5), 'Учебный класс')
        ]
        
        for i, (title, desc, date, loc) in enumerate(events):
            Event.objects.create(
                title=title,
                slug=f'test-event-{i}',
                description=desc,
                start_date=date,
                end_date=date + timedelta(hours=2),
                location=loc,
                event_type='service' if i == 0 else ('youth' if i == 1 else 'other')
            )

        self.stdout.write('Creating Kids Content...')
        kids = [
            ('Урок 1: Сотворение мира', 'Учим, как Бог создал землю.', '3-6', 'video'),
            ('Раскраска: Ноев ковчег', 'Распечатай и раскрась.', '3-6', 'pdf'),
            ('Урок: Давид и Голиаф', 'Смелость в Боге.', '7-12', 'video'),
            ('Задания на дом', 'Ребусы по библии.', '7-12', 'pdf')
        ]
        
        for i, (title, desc, age, ctype) in enumerate(kids):
            KidsContent.objects.create(
                title=title,
                description=desc,
                age_group=age,
                content_type=ctype,
                views_count=random.randint(50, 500)
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded Library data!'))
