from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from payments.models import AutomaticPaymentTemplate


class Command(BaseCommand):
    help = 'Create default automatic payment templates for colivers'

    def handle(self, *args, **options):
        self.stdout.write("Setting up default automatic payment templates...")

        # Get or create a system user for creating templates
        admin_user, created = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )

        # Template 1: Full booking payment due on arrival
        template1, created1 = AutomaticPaymentTemplate.objects.get_or_create(
            title="Booking Payment",
            defaults={
                'description_template': "Full booking payment for {coliver_name} stay at {chapter_name} ({arrival_date} to {departure_date})",
                'date_type': 'arrival_date',
                'days_offset': 0,  # Due on arrival date
                'amount_type': 'total_cost',
                'is_active': True,
                'applies_to_all_colivers': True,
                'created_by': admin_user
            }
        )
        
        if created1:
            self.stdout.write(self.style.SUCCESS(f"✓ Created template: {template1.title}"))
        else:
            self.stdout.write(f"- Template already exists: {template1.title}")

        # Template 2: Security deposit (fixed amount) due 7 days before arrival
        template2, created2 = AutomaticPaymentTemplate.objects.get_or_create(
            title="Security Deposit",
            defaults={
                'description_template': "Security deposit for {coliver_name} stay at {chapter_name}",
                'date_type': 'arrival_date',
                'days_offset': -7,  # Due 7 days before arrival
                'amount_type': 'fixed',
                'fixed_amount': 100000,  # 100,000 KRW
                'is_active': True,
                'applies_to_all_colivers': True,
                'created_by': admin_user
            }
        )
        
        if created2:
            self.stdout.write(self.style.SUCCESS(f"✓ Created template: {template2.title}"))
        else:
            self.stdout.write(f"- Template already exists: {template2.title}")

        # Template 3: 50% upfront payment due 2 weeks before arrival
        template3, created3 = AutomaticPaymentTemplate.objects.get_or_create(
            title="Upfront Payment (50%)",
            defaults={
                'description_template': "50% upfront payment for {coliver_name} booking at {chapter_name}",
                'date_type': 'arrival_date',
                'days_offset': -14,  # Due 2 weeks before arrival
                'amount_type': 'percentage_cost',
                'percentage': 50.00,
                'is_active': False,  # Disabled by default, admin can enable if needed
                'applies_to_all_colivers': True,
                'created_by': admin_user
            }
        )
        
        if created3:
            self.stdout.write(self.style.SUCCESS(f"✓ Created template: {template3.title} (disabled by default)"))
        else:
            self.stdout.write(f"- Template already exists: {template3.title}")

        # Template 4: Final checkout payment due on departure
        template4, created4 = AutomaticPaymentTemplate.objects.get_or_create(
            title="Checkout Payment",
            defaults={
                'description_template': "Final checkout payment for {coliver_name} at {chapter_name}",
                'date_type': 'departure_date',
                'days_offset': 0,  # Due on departure date
                'amount_type': 'fixed',
                'fixed_amount': 50000,  # 50,000 KRW for cleaning/processing
                'is_active': False,  # Disabled by default
                'applies_to_all_colivers': True,
                'created_by': admin_user
            }
        )
        
        if created4:
            self.stdout.write(self.style.SUCCESS(f"✓ Created template: {template4.title} (disabled by default)"))
        else:
            self.stdout.write(f"- Template already exists: {template4.title}")

        self.stdout.write(
            self.style.SUCCESS(
                "\nDefault payment templates setup complete!\n"
                "You can now:\n"
                "1. Go to Django admin > Payments > Automatic payment templates\n"
                "2. Edit the templates to match your needs\n"
                "3. Enable/disable templates as needed\n"
                "4. Use 'Generate Payments' button to create payments for existing colivers\n"
                "5. New colivers will automatically get payments based on active templates"
            )
        ) 