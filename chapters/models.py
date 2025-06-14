from django.db import models
from django.contrib.auth.models import User
from userprofile.models import Userprofile
from decimal import Decimal

class PricingTier(models.Model):
    """
    Defines pricing tiers for chapters based on length of stay.
    Each tier specifies a duration and price per night for that duration.
    """
    chapter = models.ForeignKey('Chapter', related_name='pricing_tiers', on_delete=models.CASCADE)
    tier_name = models.CharField(
        max_length=100,
        help_text="Name for this pricing tier (e.g., 'Short-term', 'Mid-term', 'Long-term')"
    )
    duration_days = models.IntegerField(
        help_text="Number of days this tier covers (e.g., 84 for first 84 days)"
    )
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per night for this tier in KRW"
    )
    tier_order = models.IntegerField(
        default=1,
        help_text="Order of this tier (1 = first tier, 2 = second tier, etc.)"
    )
    
    class Meta:
        ordering = ['chapter', 'tier_order']
        unique_together = ['chapter', 'tier_order']
    
    def __str__(self):
        return f"{self.chapter.name} - {self.tier_name} ({self.duration_days} days @ ₩{self.price_per_night}/night)"

class Chapter(models.Model):
    TEXT_SIZE_CHOICES = [
        ('xs', 'Extra Small'),
        ('sm', 'Small'),
        ('base', 'Normal'),
        ('lg', 'Large'),
        ('xl', 'Extra Large'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    description_text_size = models.CharField(
        max_length=10,
        choices=TEXT_SIZE_CHOICES,
        default='sm',
        help_text="Choose the text size for the chapter description"
    )
    cost_per_night = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Legacy cost per night in KRW (used when no pricing tiers are defined)",
        default=0.00
    )
    use_tiered_pricing = models.BooleanField(
        default=False,
        help_text="Enable tiered pricing based on length of stay. If disabled, uses the legacy cost_per_night."
    )
    
    # Short-term stay pricing
    use_short_term_pricing = models.BooleanField(
        default=False,
        help_text="Enable special pricing for very short stays (under the threshold)."
    )
    short_term_threshold_days = models.IntegerField(
        default=7,
        help_text="Maximum number of days to qualify for short-term pricing (e.g., 7 days)"
    )
    short_term_price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Special price per night for short-term stays in KRW"
    )

    created_by = models.ForeignKey(User, related_name='chapters', on_delete=models.CASCADE)
    booked_by = models.ForeignKey(Userprofile, related_name='booked_chapters', on_delete=models.CASCADE, blank=True, null=True)

    def calculate_tiered_cost(self, total_nights):
        """
        Calculate the total cost using tiered pricing, short-term pricing, or legacy pricing.
        Returns the total cost for the given number of nights.
        """
        # Check for short-term pricing first
        if (self.use_short_term_pricing and 
            total_nights <= self.short_term_threshold_days and 
            self.short_term_price_per_night > 0):
            return Decimal(str(self.short_term_price_per_night)) * Decimal(str(total_nights))
        
        # Use tiered pricing if enabled and available
        if self.use_tiered_pricing and self.pricing_tiers.exists():
            total_cost = Decimal('0.00')
            remaining_nights = total_nights
            
            # Get all pricing tiers ordered by tier_order
            tiers = self.pricing_tiers.all().order_by('tier_order')
            
            for tier in tiers:
                if remaining_nights <= 0:
                    break
                    
                # Calculate nights for this tier
                nights_in_tier = min(remaining_nights, tier.duration_days)
                tier_cost = tier.price_per_night * Decimal(str(nights_in_tier))
                total_cost += tier_cost
                remaining_nights -= nights_in_tier
            
            # If there are still remaining nights after all tiers,
            # use the last tier's price for the remaining nights
            if remaining_nights > 0 and tiers.exists():
                last_tier = tiers.last()
                additional_cost = last_tier.price_per_night * Decimal(str(remaining_nights))
                total_cost += additional_cost
            
            return round(total_cost, 2)
        
        # Fall back to legacy pricing
        return self.cost_per_night * Decimal(str(total_nights))
    
    def get_display_rate_per_night(self, total_nights):
        """
        Get the appropriate rate per night to display in the frontend.
        For short-term stays: returns short-term rate
        For tiered pricing: returns first tier rate
        Otherwise: returns legacy rate
        """
        # Check for short-term pricing first
        if (self.use_short_term_pricing and 
            total_nights <= self.short_term_threshold_days and 
            self.short_term_price_per_night > 0):
            return Decimal(str(self.short_term_price_per_night))
        
        # Use first tier rate if tiered pricing is enabled
        if self.use_tiered_pricing and self.pricing_tiers.exists():
            first_tier = self.pricing_tiers.order_by('tier_order').first()
            return first_tier.price_per_night
        
        # Fall back to legacy pricing
        return self.cost_per_night
    
    def get_pricing_breakdown(self, total_nights):
        """
        Get a detailed breakdown of pricing for the given number of nights.
        Returns a list of dictionaries with tier information and costs.
        """
        # Check for short-term pricing first
        if (self.use_short_term_pricing and 
            total_nights <= self.short_term_threshold_days and 
            self.short_term_price_per_night > 0):
            return [{
                'tier_name': f'Short-term Rate (≤{self.short_term_threshold_days} days)',
                'nights': total_nights,
                'price_per_night': Decimal(str(self.short_term_price_per_night)),
                'total_cost': Decimal(str(self.short_term_price_per_night)) * Decimal(str(total_nights))
            }]
        
        # Use tiered pricing if enabled and available
        if self.use_tiered_pricing and self.pricing_tiers.exists():
            breakdown = []
            remaining_nights = total_nights
            
            tiers = self.pricing_tiers.all().order_by('tier_order')
            
            for tier in tiers:
                if remaining_nights <= 0:
                    break
                    
                nights_in_tier = min(remaining_nights, tier.duration_days)
                tier_cost = tier.price_per_night * Decimal(str(nights_in_tier))
                
                breakdown.append({
                    'tier_name': tier.tier_name,
                    'nights': nights_in_tier,
                    'price_per_night': tier.price_per_night,
                    'total_cost': tier_cost
                })
                
                remaining_nights -= nights_in_tier
            
            # Handle remaining nights with last tier pricing
            if remaining_nights > 0 and tiers.exists():
                last_tier = tiers.last()
                additional_cost = last_tier.price_per_night * Decimal(str(remaining_nights))
                
                breakdown.append({
                    'tier_name': f'{last_tier.tier_name} (Extended)',
                    'nights': remaining_nights,
                    'price_per_night': last_tier.price_per_night,
                    'total_cost': additional_cost
                })
            
            return breakdown
        
        # Fall back to legacy pricing
        return [{
            'tier_name': 'Standard Rate',
            'nights': total_nights,
            'price_per_night': self.cost_per_night,
            'total_cost': self.cost_per_night * Decimal(str(total_nights))
        }]

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.created_by_id:
            raise ValueError("Chapter must have a created_by user.")
        if not self.created_by.is_staff:
            raise PermissionError("Only admin users can create chapters.")
        super().save(*args, **kwargs)

class ChapterBooking(models.Model):
    chapter = models.ForeignKey(Chapter, related_name='bookings', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    
    class Meta:
        ordering = ['start_date']
        
    def __str__(self):
        return f"{self.chapter.name}: {self.start_date} to {self.end_date}"

class ChapterImage(models.Model):
    chapter = models.ForeignKey(
        Chapter, 
        related_name='images', 
        on_delete=models.CASCADE
    )
    image = models.ImageField(
        upload_to='chapter_images/',
        help_text="Upload an image for this chapter"
    )
    order = models.IntegerField(
        default=0,
        help_text="Order in which the image will be displayed"
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.chapter.name}"
