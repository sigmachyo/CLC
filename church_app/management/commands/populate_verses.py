from django.core.management.base import BaseCommand
from church_app.models import DailyVerse
from datetime import date, timedelta


# Набор стихов для автозаполнения
VERSES = [
    {
        'verse_text': 'Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного, дабы всякий, верующий в Него, не погиб, но имел жизнь вечную.',
        'reference': 'Иоанна 3:16',
        'reflection': 'Любовь Божья безгранична — она открыта каждому, кто верит.',
    },
    {
        'verse_text': 'Господь — Пастырь мой; я ни в чём не буду нуждаться.',
        'reference': 'Псалом 22:1',
        'reflection': 'Бог заботится обо всех наших нуждах, когда мы доверяем Ему.',
    },
    {
        'verse_text': 'Я есмь путь и истина и жизнь; никто не приходит к Отцу, как только через Меня.',
        'reference': 'Иоанна 14:6',
        'reflection': 'Иисус — единственный путь к Богу. В Нём мы находим истину.',
    },
    {
        'verse_text': 'Всё могу в укрепляющем меня Иисусе Христе.',
        'reference': 'Филиппийцам 4:13',
        'reflection': 'Наша сила — не в нас самих, а в Том, Кто даёт нам силу.',
    },
    {
        'verse_text': 'Не бойся, ибо Я с тобою; не смущайся, ибо Я Бог твой; Я укреплю тебя, и помогу тебе.',
        'reference': 'Исаия 41:10',
        'reflection': 'Страх отступает, когда мы помним о присутствии Бога.',
    },
    {
        'verse_text': 'Притом знаем, что любящим Бога, призванным по Его изволению, всё содействует ко благу.',
        'reference': 'Римлянам 8:28',
        'reflection': 'Даже трудности служат нашему благу в Божьем плане.',
    },
    {
        'verse_text': 'Надейся на Господа всем сердцем твоим, и не полагайся на разум твой.',
        'reference': 'Притчи 3:5',
        'reflection': 'Доверие Богу превыше человеческой мудрости.',
    },
    {
        'verse_text': 'Ибо Я знаю намерения, какие имею о вас, говорит Господь, намерения во благо, а не на зло, чтобы дать вам будущность и надежду.',
        'reference': 'Иеремия 29:11',
        'reflection': 'У Бога есть план для каждого из нас — план надежды и будущего.',
    },
    {
        'verse_text': 'Бог нам прибежище и сила, скорый помощник в бедах.',
        'reference': 'Псалом 45:2',
        'reflection': 'В любых обстоятельствах мы можем обратиться к Богу за помощью.',
    },
    {
        'verse_text': 'Кто во Христе, тот новая тварь; древнее прошло, теперь всё новое.',
        'reference': '2 Коринфянам 5:17',
        'reflection': 'Во Христе каждый день — новое начало.',
    },
    {
        'verse_text': 'Придите ко Мне, все труждающиеся и обременённые, и Я успокою вас.',
        'reference': 'Матфея 11:28',
        'reflection': 'Иисус приглашает нас к Себе с любой усталостью и тяжестью.',
    },
    {
        'verse_text': 'Ищите же прежде Царства Божия и правды Его, и это всё приложится вам.',
        'reference': 'Матфея 6:33',
        'reflection': 'Приоритет Бога в нашей жизни — ключ ко всему остальному.',
    },
    {
        'verse_text': 'Любовь долготерпит, милосердствует, любовь не завидует, любовь не превозносится, не гордится.',
        'reference': '1 Коринфянам 13:4',
        'reflection': 'Настоящая любовь проявляется в терпении и смирении.',
    },
    {
        'verse_text': 'Мир оставляю вам, мир Мой даю вам; не так, как мир даёт, Я даю вам.',
        'reference': 'Иоанна 14:27',
        'reflection': 'Мир от Бога — это внутренний покой, который не зависит от обстоятельств.',
    },
]


class Command(BaseCommand):
    help = 'Заполняет стихи дня (DailyVerse) на ближайшие 14 дней'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=14,
            help='Количество дней для заполнения (по умолчанию 14)',
        )

    def handle(self, *args, **options):
        days = options['days']
        today = date.today()
        created = 0

        for i in range(days):
            target_date = today + timedelta(days=i)
            verse_data = VERSES[i % len(VERSES)]

            _, was_created = DailyVerse.objects.get_or_create(
                date=target_date,
                defaults={
                    'verse_text': verse_data['verse_text'],
                    'reference': verse_data['reference'],
                    'reflection': verse_data['reflection'],
                },
            )
            if was_created:
                created += 1
                self.stdout.write(f'  [OK] {target_date} — {verse_data["reference"]}')
            else:
                self.stdout.write(f'  [SKIP] {target_date} — уже есть')

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово! Создано {created} новых стихов из {days} дней.'
        ))
