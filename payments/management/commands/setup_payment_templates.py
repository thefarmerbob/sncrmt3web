from django.core.management.base import BaseCommand
from payments.models import AutomaticPaymentTemplate


class Command(BaseCommand):
    help = 'Create default automatic payment templates'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up default payment templates...'))
        
        # Security Deposit Template
        security_template, created = AutomaticPaymentTemplate.objects.get_or_create(
            title='Security Deposit',
            defaults={
                'description_template': 'Security deposit for {coliver_name} stay at {chapter_name}',
                'amount_type': 'fixed',
                'fixed_amount': 100000.00,  # ₩100,000
                'date_type': 'arrival_date',
                'days_offset': -7,  # Due 7 days before arrival
                'is_active': True,
                'applies_to_all_colivers': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Security Deposit template (₩{security_template.fixed_amount:,.0f})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Security Deposit template already exists')
            )
        
        # Booking Payment Template
        booking_template, created = AutomaticPaymentTemplate.objects.get_or_create(
            title='Booking Payment',
            defaults={
                'description_template': 'Full booking payment for {coliver_name} stay at {chapter_name} ({arrival_date} to {departure_date})',
                'amount_type': 'total_cost',
                'date_type': 'arrival_date',
                'days_offset': 0,  # Due on arrival date
                'is_active': True,
                'applies_to_all_colivers': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Booking Payment template (Total Stay Cost)')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Booking Payment template already exists')
            )
        
        # Summary
        total_templates = AutomaticPaymentTemplate.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Setup complete! {total_templates} active payment templates configured.')
        )
        
        self.stdout.write(
            self.style.SUCCESS('\nNow when an application status changes to "Onboarding":')
        )
        self.stdout.write(
            self.style.SUCCESS('  1. A coliver record will be created automatically')
        )
        self.stdout.write(
            self.style.SUCCESS('  2. Security deposit and booking payment invoices will be generated')
        )
        self.stdout.write(
            self.style.SUCCESS('  3. Payments will have appropriate due dates and amounts')
        ) 