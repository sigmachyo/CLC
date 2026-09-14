from django.core.management.base import BaseCommand
from church_app.models import PrayerRequest, Event

class Command(BaseCommand):
    help = 'Cleans up test data from the database (admin prayer requests, bad event times)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Do not actually delete anything, just show what would be deleted',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # 1. Найти молитвенные нужды от admin, содержащие "test" или подозрительные
        admin_prayers = PrayerRequest.objects.filter(user__username='admin')
        if admin_prayers.exists():
            self.stdout.write(self.style.WARNING(f'Found {admin_prayers.count()} prayer requests from admin:'))
            for p in admin_prayers:
                self.stdout.write(f'  - [{p.id}] {p.title}')
            
            if not dry_run:
                deleted, _ = admin_prayers.delete()
                self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} admin prayer requests.'))
        else:
            self.stdout.write('No admin prayer requests found.')

        # 2. Найти события с временем 06:06 или 05:59
        bad_events = []
        for event in Event.objects.all():
            if (event.start_date.hour == 6 and event.start_date.minute == 6) or \
               (event.start_date.hour == 5 and event.start_date.minute == 59):
                bad_events.append(event)
        
        if bad_events:
            self.stdout.write(self.style.WARNING(f'\nFound {len(bad_events)} events with suspicious times (06:06 or 05:59):'))
            for e in bad_events:
                self.stdout.write(f'  - [{e.id}] {e.title} at {e.start_date.strftime("%Y-%m-%d %H:%M")}')
            
            self.stdout.write(self.style.NOTICE('Please update these events manually in the admin panel.'))
        else:
            self.stdout.write('\nNo events with suspicious times found.')
