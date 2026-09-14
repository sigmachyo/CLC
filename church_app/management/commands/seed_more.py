import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from church_app.models import Category, Video, Event, KidsContent, DailyVerse, BiblePlan, BibleReading, UserBibleProgress
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Seeds more detailed test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Adding Bible Plans...')
        
        # User
        user, _ = User.objects.get_or_create(username='testuser', email='test@test.com', defaults={'password': 'password'})

        # Bible Categories
        cat_bible, _ = Category.objects.get_or_create(name='Библия', slug='bible', defaults={'description': 'Библейские планы', 'category_type': 'bible'})
        cat_events, _ = Category.objects.get_or_create(name='События', slug='events', defaults={'description': 'Мероприятия', 'category_type': 'events'})

        # Plans
        plan1, _ = BiblePlan.objects.get_or_create(title='Основы веры', defaults={'description': 'План для новых верующих', 'days_count': 3, 'is_active': True})
        plan2, _ = BiblePlan.objects.get_or_create(title='Евангелие от Иоанна', defaults={'description': 'Чтение Евангелия от Иоанна', 'days_count': 7, 'is_active': True})
        
        for i in range(1, 4):
            BibleReading.objects.get_or_create(plan=plan1, day_number=i, defaults={'title': f'Основы День {i}', 'bible_passage': 'Бытие 1:1', 'content': 'Тестовое чтение для дня ' + str(i)})
            
        for i in range(1, 8):
            BibleReading.objects.get_or_create(plan=plan2, day_number=i, defaults={'title': f'Иоанн День {i}', 'bible_passage': f'Иоанна {i}', 'content': 'Тестовое чтение для дня ' + str(i)})

        UserBibleProgress.objects.get_or_create(user=user, plan=plan1, defaults={'current_day': 1})

        # Kids Content
        KidsContent.objects.all().delete()
        kids = [
            ('Мультик: Суперкнига', 'Новые приключения.', '3-5', 'cartoon'),
            ('Урок: Вера Давида', 'Учимся доверять Богу.', '6-9', 'lesson'),
            ('Игра: Библейское лото', 'Найди пару.', '3-5', 'game'),
            ('Поделка: Ковчег', 'Сделай сам.', '6-9', 'craft'),
            ('Песня: Иисус любит меня', 'Поем вместе.', '3-5', 'song'),
        ]
        
        for title, desc, age, ctype in kids:
            KidsContent.objects.create(
                title=title,
                description=desc,
                age_group=age,
                content_type=ctype,
                youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                views_count=random.randint(50, 500)
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded more data!'))
