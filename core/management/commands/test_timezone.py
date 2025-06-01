from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import pytz

class Command(BaseCommand):
    help = 'Test timezone configuration'

    def handle(self, *args, **options):
        # Get current time in different formats
        now_utc = timezone.now()
        now_local = timezone.localtime(now_utc)
        
        self.stdout.write(self.style.SUCCESS(f'Django TIME_ZONE setting: {settings.TIME_ZONE}'))
        self.stdout.write(self.style.SUCCESS(f'Django USE_TZ setting: {settings.USE_TZ}'))
        self.stdout.write(f'Current UTC time: {now_utc}')
        self.stdout.write(f'Current local time (KST): {now_local}')
        self.stdout.write(f'Timezone info: {now_local.tzinfo}')
        
        # Test KST timezone specifically
        kst = pytz.timezone('Asia/Seoul')
        now_kst = now_utc.astimezone(kst)
        self.stdout.write(f'Current KST time: {now_kst}')
        
        # Test timezone.now() behavior
        self.stdout.write(f'timezone.now() returns: {timezone.now()}')
        self.stdout.write(f'timezone.now().date() returns: {timezone.now().date()}')
        
        self.stdout.write(self.style.SUCCESS('Timezone test completed successfully!')) 