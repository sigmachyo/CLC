from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from .models import DailyVerse, PrayerRequest
from .forms import RegisterForm, PrayerRequestForm


class FormTests(TestCase):
    """Тесты для Django Forms"""
    
    def test_register_form_valid(self):
        form = RegisterForm(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertTrue(form.is_valid())
    
    def test_register_form_passwords_mismatch(self):
        form = RegisterForm(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!',
        })
        self.assertFalse(form.is_valid())
    
    def test_register_form_short_password(self):
        form = RegisterForm(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'Short1!',
            'password2': 'Short1!',
        })
        self.assertFalse(form.is_valid())
    
    def test_register_form_duplicate_username(self):
        User.objects.create_user('existing', 'e@e.com', 'ExistingPass123!')
        form = RegisterForm(data={
            'username': 'existing',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertFalse(form.is_valid())
    
    def test_prayer_form_valid(self):
        form = PrayerRequestForm(data={
            'title': 'Тестовая молитва',
            'description': 'Описание нужды',
            'is_public': True,
        })
        self.assertTrue(form.is_valid())
    
    def test_prayer_form_empty_title(self):
        form = PrayerRequestForm(data={
            'title': '',
            'description': 'Описание',
            'is_public': True,
        })
        self.assertFalse(form.is_valid())


class ViewTests(TestCase):
    """Тесты для основных Views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpassword123',
        )
    
    def test_home_page_status(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_prayer_list_status(self):
        response = self.client.get(reverse('prayer_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_page_status(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    
    def test_register_page_status(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
    
    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
    
    def test_profile_authenticated(self):
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)


class DailyVerseTests(TestCase):
    """Тесты для DailyVerse"""
    
    def test_daily_verse_in_library_context(self):
        DailyVerse.objects.create(
            verse_text='Тестовый стих',
            reference='Тест 1:1',
            date=date.today(),
        )
        response = self.client.get(reverse('library_home'))
        self.assertIsNotNone(response.context.get('daily_verse'))
        self.assertEqual(response.context['daily_verse'].reference, 'Тест 1:1')
    
    def test_daily_verse_fallback(self):
        """Если нет стиха на сегодня, берётся последний добавленный"""
        DailyVerse.objects.create(
            verse_text='Вчерашний стих',
            reference='Вчера 1:1',
            date=date.today() - timedelta(days=1),
        )
        response = self.client.get(reverse('library_home'))
        verse = response.context.get('daily_verse')
        self.assertIsNotNone(verse)
        self.assertEqual(verse.reference, 'Вчера 1:1')
    
    def test_no_daily_verse(self):
        """Без стихов в базе — daily_verse == None"""
        response = self.client.get(reverse('library_home'))
        self.assertIsNone(response.context.get('daily_verse'))


class PrayerSupportTests(TestCase):
    """Тест защиты от повторного голосования"""
    
    def setUp(self):
        self.user = User.objects.create_user('voter', 'v@v.com', 'pass12345')
        self.prayer = PrayerRequest.objects.create(
            user=self.user,
            title='Нужда',
            description='Описание',
            is_public=True,
            prayer_count=0,
        )
    
    def test_prayer_support_increments(self):
        self.client.login(username='voter', password='pass12345')
        self.client.post(reverse('prayer_support', args=[self.prayer.id]))
        self.prayer.refresh_from_db()
        self.assertEqual(self.prayer.prayer_count, 1)
    
    def test_prayer_support_no_duplicate(self):
        self.client.login(username='voter', password='pass12345')
        self.client.post(reverse('prayer_support', args=[self.prayer.id]))
        self.client.post(reverse('prayer_support', args=[self.prayer.id]))
        self.prayer.refresh_from_db()
        self.assertEqual(self.prayer.prayer_count, 1)