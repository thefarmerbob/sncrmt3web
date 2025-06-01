from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from payments.models import AutomaticPaymentTemplate, AutomaticPayment
from colivers.models import Coliver


class Command(BaseCommand):
    help = 'Generate automatic payments for all existing colivers based on active templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating payments',
        )
        parser.add_argument(
            '--template-id',
            type=int,
            help='Only create payments for a specific template ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        template_id = options.get('template_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No payments will be created"))
        
        # Get active templates
        if template_id:
            templates = AutomaticPaymentTemplate.objects.filter(id=template_id, is_active=True)
            if not templates.exists():
                self.stdout.write(self.style.ERROR(f"Template with ID {template_id} not found or not active"))
                return
        else:
            templates = AutomaticPaymentTemplate.objects.filter(is_active=True, applies_to_all_colivers=True)
        
        if not templates.exists():
            self.stdout.write(self.style.WARNING("No active templates found that apply to all colivers"))
            return
        
        # Get all active colivers
        colivers = Coliver.objects.filter(is_active=True)
        
        self.stdout.write(f"Found {templates.count()} active template(s) and {colivers.count()} active coliver(s)")
        
        total_created = 0
        total_existing = 0
        
        for template in templates:
            self.stdout.write(f"\nProcessing template: {template.title}")
            created_for_template = 0
            existing_for_template = 0
            
            for coliver in colivers:
                # Check if payment already exists
                existing_payment = AutomaticPayment.objects.filter(
                    template=template,
                    coliver=coliver
                ).first()
                
                if existing_payment:
                    existing_for_template += 1
                    continue
                
                if not dry_run:
                    # Create the payment
                    payment = template.create_payment_for_coliver(coliver)
                    if payment:
                        created_for_template += 1
                        self.stdout.write(f"  ✓ Created payment for {coliver.first_name} {coliver.last_name}")
                    else:
                        self.stdout.write(f"  ✗ Failed to create payment for {coliver.first_name} {coliver.last_name}")
                else:
                    # Dry run - just show what would be created
                    amount = template.calculate_amount(coliver)
                    due_date = template.calculate_due_date(coliver)
                    created_for_template += 1
                    self.stdout.write(
                        f"  [DRY RUN] Would create payment for {coliver.first_name} {coliver.last_name}: "
                        f"₩{amount:,.2f} due {due_date}"
                    )
            
            self.stdout.write(f"  Template '{template.title}': {created_for_template} created, {existing_for_template} already exist")
            total_created += created_for_template
            total_existing += existing_for_template
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary:\n"
                f"- Total payments {'would be created' if dry_run else 'created'}: {total_created}\n"
                f"- Total payments already existing: {total_existing}"
            )
        )
        
        if dry_run and total_created > 0:
            self.stdout.write(
                self.style.WARNING(
                    "Run the command without --dry-run to actually create the payments"
                )
            ) 