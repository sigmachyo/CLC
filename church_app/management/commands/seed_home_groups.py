from django.core.management.base import BaseCommand
from church_app.models import HomeGroup

class Command(BaseCommand):
    help = 'Заполняет базу данных домашними группами'

    def handle(self, *args, **options):
        # Удаляем старые записи (опционально)
        HomeGroup.objects.all().delete()
        
        groups = [
            # СОВЕТСКИЙ РАЙОН
            {'district': 'Советский район', 'address': 'ул. 40 лет Победы, 12', 'group_type': 'female', 'day': 'wednesday', 'time': '14:00', 'age_display': ''},
            {'district': 'Советский район', 'address': 'ул. Тельмана, 18а', 'group_type': 'mixed', 'day': 'negotiable', 'time': '19:00', 'age_display': '28-70'},
            {'district': 'Советский район', 'address': 'ул. Краснодарская, 3', 'group_type': 'female', 'day': 'negotiable', 'time': '', 'age_display': '40-70'},
            {'district': 'Советский район', 'address': 'пр. Металлургов, 30а', 'group_type': 'mixed', 'day': 'friday', 'time': '19:00', 'age_display': ''},
            {'district': 'Советский район', 'address': 'ул. Молокова, 40', 'group_type': 'female', 'day': 'wednesday', 'time': '19:00', 'age_display': ''},
            {'district': 'Советский район', 'address': 'пр. Металлургов, 55а', 'group_type': 'mixed', 'day': 'thursday', 'time': '19:00', 'age_display': ''},
            {'district': 'Советский район', 'address': 'ул. Алексеева 24/1', 'group_type': 'mixed', 'day': 'thursday', 'time': '19:00', 'age_display': ''},
            {'district': 'Советский район', 'address': 'ул. Партизана Железняка, 3о', 'group_type': 'mixed', 'day': 'thursday', 'time': '19:00', 'age_display': ''},
            {'district': 'Советский район', 'address': 'ул. П. Подзолкова, 6', 'group_type': 'mixed', 'day': 'thursday', 'time': '19:00', 'age_display': '20-50'},
            {'district': 'Советский район', 'address': 'ул. П. Ломако, 2', 'group_type': 'female', 'day': 'monday', 'time': '19:00', 'age_display': '20-50'},
            
            # ЖЕЛЕЗНОДОРОЖНЫЙ РАЙОН
            {'district': 'Железнодорожный район', 'address': 'пр-т Свободный, 27', 'group_type': 'mixed', 'day': 'friday', 'time': '19:00', 'age_display': '20-60'},
            {'district': 'Железнодорожный район', 'address': 'ул. Куйбышева, 85', 'group_type': 'mixed', 'day': 'tuesday', 'time': '19:00', 'age_display': ''},
            {'district': 'Железнодорожный район', 'address': 'ул. Калинина, 8', 'group_type': 'mixed', 'day': 'friday', 'time': '19:00', 'age_display': '25-50'},
            {'district': 'Железнодорожный район', 'address': 'ул. Бограда, 134', 'group_type': 'mixed', 'day': 'thursday', 'time': '19:00', 'age_display': ''},
            
            # ЦЕНТРАЛЬНЫЙ РАЙОН
            {'district': 'Центральный район', 'address': 'ул. Дм. Мартынова, 25', 'group_type': 'mixed', 'day': 'wednesday', 'time': '18:30', 'age_display': '30-55'},
            {'district': 'Центральный район', 'address': 'ул. Пасхальная, 2', 'group_type': 'female', 'day': 'tuesday', 'time': '19:00', 'age_display': ''},
            {'district': 'Центральный район', 'address': 'ул. Пасхальная, 2', 'group_type': 'female', 'day': 'wednesday', 'time': '19:00', 'age_display': ''},
            
            # ОКТЯБРЬСКИЙ РАЙОН
            {'district': 'Октябрьский район', 'address': 'ул. Вербная, 5', 'group_type': 'female', 'day': 'friday', 'time': '19:00', 'age_display': ''},
            {'district': 'Октябрьский район', 'address': 'ул. Словцова, 4', 'group_type': 'mixed', 'day': 'wednesday', 'time': '19:00', 'age_display': ''},
            {'district': 'Октябрьский район', 'address': 'ул. Словцова, 4', 'group_type': 'mixed', 'day': 'thursday', 'time': '10:00', 'age_display': ''},
            
            # КИРОВСКИЙ РАЙОН
            {'district': 'Кировский район', 'address': 'ул. Мичурина, 3а', 'group_type': 'female', 'day': 'negotiable', 'time': '10:00', 'age_display': ''},
            {'district': 'Кировский район', 'address': 'ул. Вавилова, 48', 'group_type': 'female', 'day': 'tuesday', 'time': '18:30', 'age_display': ''},
            {'district': 'Кировский район', 'address': 'ул. Московская, 8', 'group_type': 'mixed', 'day': 'friday', 'time': '19:00', 'age_display': ''},
            
            # ЛЕНИНСКИЙ РАЙОН
            {'district': 'Ленинский район', 'address': 'ул. Энергетиков, 30', 'group_type': 'male', 'day': 'tuesday', 'time': '19:00', 'age_display': ''},
            
            # СВЕРДЛОВСКИЙ РАЙОН
            {'district': 'Свердловский район', 'address': 'ул. 60 лет Октября, 54', 'group_type': 'female', 'day': 'monday', 'time': '15:00', 'age_display': 'от 55'},
            {'district': 'Свердловский район', 'address': 'ул. Карамзина, 18', 'group_type': 'female', 'day': 'monday', 'time': '19:00', 'age_display': ''},
            
            # МОЛОДЕЖНЫЕ И ПОДРОСТКОВЫЕ ГРУППЫ
            {'district': 'Молодежные', 'address': 'ул. Вильского, 34', 'group_type': 'mixed', 'day': 'wednesday', 'time': '19:30', 'age_display': '16-25'},
            {'district': 'Молодежные', 'address': 'ул. Линейная, 112', 'group_type': 'mixed', 'day': 'tuesday', 'time': '19:00', 'age_display': '16-25'},
            {'district': 'Молодежные', 'address': 'ул. Перенсона, 5а', 'group_type': 'male', 'day': 'monday', 'time': '19:00', 'age_display': 'от 23'},
            {'district': 'Молодежные', 'address': 'пр-т Свободный, 76а', 'group_type': 'male', 'day': 'friday', 'time': '17:00', 'age_display': '18-22'},
            {'district': 'Молодежные', 'address': 'ул. Свердловская, 3д', 'group_type': 'mixed', 'day': 'saturday', 'time': '18:00', 'age_display': '15-25'},
            {'district': 'Молодежные', 'address': 'ул. Л.Шевцовой, 88', 'group_type': 'male', 'day': 'wednesday', 'time': '19:00', 'age_display': '18-25'},
            {'district': 'Молодежные', 'address': 'ул. Бограда, 134', 'group_type': 'female', 'day': 'monday', 'time': '19:30', 'age_display': '15-24'},
            {'district': 'Молодежные', 'address': 'ул. Алексеева, 113', 'group_type': 'mixed', 'day': 'monday', 'time': '19:00', 'age_display': '18-30'},
            {'district': 'Молодежные', 'address': 'ул. Лесников, 31', 'group_type': 'mixed', 'day': 'wednesday', 'time': '19:30', 'age_display': '16-24'},
            {'district': 'Молодежные', 'address': 'ул. Перенсона, 5а', 'group_type': 'male', 'day': 'wednesday', 'time': '19:00', 'age_display': 'от 16'},
            {'district': 'Молодежные', 'address': 'ул. Свердловская, 17б', 'group_type': 'female', 'day': 'tuesday', 'time': '19:00', 'age_display': ''},
            {'district': 'Молодежные', 'address': 'ул. Свердловская, 3д', 'group_type': 'mixed', 'day': 'thursday', 'time': '19:00', 'age_display': '14-18'},
            {'district': 'Молодежные', 'address': 'ул. Батурина', 'group_type': 'mixed', 'day': 'tuesday', 'time': '19:00', 'age_display': ''},
            {'district': 'Молодежные', 'address': 'ул. Авиаторов, 4е', 'group_type': 'mixed', 'day': 'thursday', 'time': '19:00', 'age_display': 'от 23'},
            {'district': 'Молодежные', 'address': 'ул. Вавилова, 48', 'group_type': 'mixed', 'day': 'saturday', 'time': '18:00', 'age_display': '10-14'},
        ]
        
        created = 0
        for i, data in enumerate(groups):
            group, was_created = HomeGroup.objects.get_or_create(
                district=data['district'],
                address=data['address'],
                defaults={
                    'group_type': data['group_type'],
                    'day': data['day'],
                    'time': data['time'],
                    'age_display': data['age_display'],
                    'order': i,
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
                self.stdout.write(f'[OK] {group.district} - {group.address}')
            else:
                self.stdout.write(f'[SKIP] {group.district} - {group.address} (уже существует)')
        
        self.stdout.write(self.style.SUCCESS(f'\nСоздано {created} групп из {len(groups)}'))