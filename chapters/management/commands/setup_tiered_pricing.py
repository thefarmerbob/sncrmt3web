from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chapters.models import Chapter, PricingTier


class Command(BaseCommand):
    help = 'Set up example tiered pricing for chapters'

    def handle(self, *args, **options):
        # Get or create a staff user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Create or update a chapter with tiered pricing
        chapter, created = Chapter.objects.get_or_create(
            name='Jeongwol',
            defaults={
                'description': 'A beautiful chapter in Jeongwol with stunning mountain views and modern amenities.',
                'cost_per_night': 100000.00,  # Legacy pricing
                'use_tiered_pricing': True,
                'use_short_term_pricing': True,
                'short_term_threshold_days': 7,
                'short_term_price_per_night': 139000.00,
                'created_by': admin_user
            }
        )
        
        if not created:
            chapter.use_tiered_pricing = True
            # Enable short-term pricing for stays under 7 days
            chapter.use_short_term_pricing = True
            chapter.short_term_threshold_days = 7
            chapter.short_term_price_per_night = 139000.00  # Higher rate for very short stays
            chapter.save()
        else:
            # For new chapters, also set short-term pricing
            chapter.use_short_term_pricing = True
            chapter.short_term_threshold_days = 7
            chapter.short_term_price_per_night = 139000.00
            chapter.save()

        # Clear existing pricing tiers
        chapter.pricing_tiers.all().delete()

        # Create tiered pricing structure
        pricing_tiers = [
            {
                'tier_name': 'Short-term (2 weeks)',
                'duration_days': 14,
                'price_per_night': 119000.00,
                'tier_order': 1
            },
            {
                'tier_name': 'Mid-term (4 - 12 weeks)',
                'duration_days': 70,  # 84 - 14 = 70 more days
                'price_per_night': 109000.00,
                'tier_order': 2
            },
            {
                'tier_name': 'Long-term (Monthly rate)',
                'duration_days': 999,  # Large number for remaining days
                'price_per_night': 99000.00,
                'tier_order': 3
            }
        ]

        for tier_data in pricing_tiers:
            PricingTier.objects.create(
                chapter=chapter,
                **tier_data
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up tiered pricing for chapter "{chapter.name}"'
            )
        )
        
        # Display the pricing structure
        self.stdout.write('\nPricing Structure:')
        if chapter.use_short_term_pricing:
            self.stdout.write(f'  - Short-term (≤{chapter.short_term_threshold_days} days): ₩{chapter.short_term_price_per_night:,.0f}/night')
        for tier in chapter.pricing_tiers.all():
            self.stdout.write(f'  - {tier.tier_name}: ₩{tier.price_per_night:,.0f}/night for {tier.duration_days} days')
        
        # Show example calculations
        self.stdout.write('\nExample calculations:')
        examples = [3, 7, 14, 30, 60, 90, 120]
        for nights in examples:
            total_cost = chapter.calculate_tiered_cost(nights)
            self.stdout.write(f'  - {nights} nights: ₩{total_cost:,.0f}') 