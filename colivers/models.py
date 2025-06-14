from django.db import models
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.models import User
from chapters.models import Chapter
from decimal import Decimal
from django.db.models.signals import pre_save
from django.dispatch import receiver

class Coliver(models.Model):

    COLIVER_STATUS_CHOICES = [
        ('ONBOARDING', 'Onboarding'),
        ('COLIVING', 'Coliving'),
        ('APPLICATION', 'Application'),
    ]

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    arrival_date = models.DateField()
    departure_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, null=True, default=None, on_delete=models.CASCADE)
    chapter_name = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='colivers',
        null=True,
        blank=True,
        default=None
    )
    manual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Override the automatically calculated cost. Leave empty to use calculated cost.")
    is_active = models.BooleanField(default=True, help_text="If unchecked, the coliver will be moved to the archive.")

    status = models.CharField(
        max_length=20,
        choices=COLIVER_STATUS_CHOICES,
        default='ONBOARDING'
    )

    def calculate_cost(self):
        """Calculate the total cost for the coliver's stay using tiered pricing."""
        # Only use manual_cost if it's set to a positive value
        # If manual_cost is 0 or None, use automatic calculation
        if self.manual_cost is not None and self.manual_cost > 0:
            return self.manual_cost
            
        if self.chapter_name and self.arrival_date and self.departure_date:
            nights = (self.departure_date - self.arrival_date).days
            # Use tiered pricing if enabled, otherwise fall back to legacy pricing
            base_cost = self.chapter_name.calculate_tiered_cost(nights)
            return round(base_cost, 2)
        return Decimal('0.00')

    @property
    def total_cost(self):
        """Return the formatted total cost with Korean Won sign and commas."""
        return f"₩{self.calculate_cost():,.2f}"
    
    def get_pricing_breakdown(self):
        """Get a detailed breakdown of pricing for this coliver's stay."""
        if not self.chapter_name or not self.arrival_date or not self.departure_date:
            return {
                'tiers': [],
                'adjustments': [],
                'total_nights': 0,
                'final_total': Decimal('0.00')
            }
        
        nights = (self.departure_date - self.arrival_date).days
        breakdown = self.chapter_name.get_pricing_breakdown(nights)
        
        return {
            'tiers': breakdown,
            'adjustments': [],  # Colivers don't have member discounts or guest increases
            'total_nights': nights,
            'final_total': self.calculate_cost()
        }

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['-arrival_date']

@receiver(pre_save, sender='colivers.Coliver')
def handle_coliver_status_change(sender, instance, **kwargs):
    """Handle status changes when a coliver is deactivated"""
    if instance.pk:  # Only for existing colivers
        try:
            old_instance = Coliver.objects.get(pk=instance.pk)
            if old_instance.is_active and not instance.is_active:
                # When deactivating a coliver, update their status
                instance.status = 'APPLICATION'
        except Coliver.DoesNotExist:
            pass

    

