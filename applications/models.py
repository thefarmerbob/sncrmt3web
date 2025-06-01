from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from questions.models import Question
from datetime import datetime, timedelta
from decimal import Decimal
from chapters.models import ChapterBooking
from django.core.exceptions import ValidationError

class PricingSettings(models.Model):
    member_discount = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=3.00,
        help_text="Percentage discount for returning members (e.g., 3.00 for 3%)"
    )
    guest_increase = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.00,
        help_text="Percentage increase for second guest (e.g., 20.00 for 20%)"
    )
    pricing_info_title = models.CharField(
        max_length=200, 
        default="How Prices Are Calculated"
    )
    base_price_text = models.CharField(
        max_length=200, 
        default="The nightly rate × number of nights"
    )
    member_discount_text = models.CharField(
        max_length=200, 
        default="Returning members receive a {discount}% discount on the total price"
    )
    guest_increase_text = models.CharField(
        max_length=200, 
        default="Selecting 2 guests adds a {increase}% increase to the total combined price for both guests"
    )
    calculation_note = models.TextField(
        default="Discounts and increases are calculated sequentially. For returning members with 2 guests, "
                "the {discount}% discount is applied first, followed by the {increase}% increase for the second guest."
    )

    class Meta:
        verbose_name = "Pricing Settings"
        verbose_name_plural = "Pricing Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and PricingSettings.objects.exists():
            return
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        settings = cls.objects.first()
        if not settings:
            settings = cls.objects.create()
        return settings

    def get_member_discount_decimal(self):
        return self.member_discount / Decimal('100.0')

    def get_guest_increase_decimal(self):
        return self.guest_increase / Decimal('100.0')

    def get_formatted_texts(self):
        return {
            'title': self.pricing_info_title,
            'base_price': self.base_price_text,
            'member_discount': self.member_discount_text.format(discount=self.member_discount),
            'guest_increase': self.guest_increase_text.format(increase=self.guest_increase),
            'note': self.calculation_note.format(discount=self.member_discount, increase=self.guest_increase)
        }

class Application(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Withdrawn', 'Withdrawn'),
    ]

    APPLICATION_STATUS_CHOICES = [
        ('Approved for interview', 'Approved for interview'),
        ('Scheduled interview', 'Scheduled interview'),
        ('Interview passed', 'Interview passed'),
        ('Rejected', 'Rejected'),
        ('Accepted', 'Accepted'),
        ('Waiting list', 'Waiting list'),
        ('Application in progress', 'Application in progress'),
        ('Submitted', 'Submitted'),
        ('Withdrawn', 'Withdrawn'),
        ('Onboarding', 'Onboarding'),
    ]

    MEMBER_TYPE_CHOICES = [
        ('new member', 'new member'),
        ('returning member', 'returning member'),
    ]

    GUESTS_CHOICES = [
        ('1', '1'),
        ('2', '2'),
    ]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='applications', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    date_join = models.DateField(verbose_name='Arrival Date', null=True, blank=True)
    date_leave = models.DateField(verbose_name='Departure Date', null=True, blank=True)
    member_type = models.CharField(max_length=20, choices=MEMBER_TYPE_CHOICES, default='new member')
    guests = models.CharField(max_length=2, choices=GUESTS_CHOICES, default='1')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    application_status = models.CharField(max_length=40, choices=APPLICATION_STATUS_CHOICES, default='Application in progress')
    chapter = models.ForeignKey('chapters.Chapter', on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    manual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Override the automatically calculated cost. Leave empty to use calculated cost.")
    is_active = models.BooleanField(default=True, help_text="If unchecked, the application will be moved to the archive.")
    
    # Reintroduction fields for returning members
    wants_reintroduction = models.BooleanField(null=True, blank=True, help_text="Whether the returning member wants to reintroduce themselves")
    reintroduction_completed = models.BooleanField(default=False, help_text="Whether the reintroduction form has been completed")

    def clean(self):
        super().clean()
        if self.date_join and self.date_leave:
            if self.date_leave <= self.date_join:
                raise ValidationError('Departure date must be after arrival date.')
            
            # Check if stay duration exceeds 93 days
            days_difference = (self.date_leave - self.date_join).days
            if days_difference > 93:
                raise ValidationError('Initial bookings are limited to 93 days (3 months). You can extend your stay after arrival if space is available.')

    def calculate_cost(self):
        if self.manual_cost is not None:
            return self.manual_cost
            
        if self.chapter and self.date_join and self.date_leave:
            settings = PricingSettings.get_settings()
            nights = (self.date_leave - self.date_join).days
            
            # Use tiered pricing if enabled, otherwise fall back to legacy pricing
            base_cost = self.chapter.calculate_tiered_cost(nights)
            print(f"Initial base cost (tiered): {base_cost}")
            print(f"Member type: {self.member_type}")
            print(f"Number of guests: {self.guests}")
            
            # Apply member discount for returning members
            if self.member_type == 'returning member':
                discount = round(base_cost * settings.get_member_discount_decimal(), 2)
                base_cost = base_cost - discount
                print(f"After returning member discount ({settings.member_discount}%): {base_cost}")
            
            # Apply increase for 2 guests
            if self.guests == '2':
                increase = round(base_cost * settings.get_guest_increase_decimal(), 2)
                base_cost = base_cost + increase
                print(f"After guest increase ({settings.guest_increase}%): {base_cost}")
            
            return round(base_cost, 2)
        return Decimal('0.00')

    @property
    def total_cost(self):
        """Return the formatted total cost with Korean Won sign and commas."""
        return f"₩{self.calculate_cost():,.2f}"
    
    def get_pricing_breakdown(self):
        """Get a detailed breakdown of pricing for this application."""
        if not self.chapter or not self.date_join or not self.date_leave:
            return []
        
        nights = (self.date_leave - self.date_join).days
        breakdown = self.chapter.get_pricing_breakdown(nights)
        
        # Apply member discount and guest increase to the breakdown
        settings = PricingSettings.get_settings()
        
        # Calculate total before adjustments
        total_before_adjustments = sum(item['total_cost'] for item in breakdown)
        
        # Add adjustment information
        adjustments = []
        
        if self.member_type == 'returning member':
            discount_amount = round(total_before_adjustments * settings.get_member_discount_decimal(), 2)
            adjustments.append({
                'type': 'discount',
                'name': f'Returning Member Discount ({settings.member_discount}%)',
                'amount': -discount_amount
            })
        
        if self.guests == '2':
            # Calculate increase on the amount after member discount
            amount_after_discount = total_before_adjustments
            if self.member_type == 'returning member':
                amount_after_discount -= round(total_before_adjustments * settings.get_member_discount_decimal(), 2)
            
            increase_amount = round(amount_after_discount * settings.get_guest_increase_decimal(), 2)
            adjustments.append({
                'type': 'increase',
                'name': f'Second Guest Increase ({settings.guest_increase}%)',
                'amount': increase_amount
            })
        
        return {
            'tiers': breakdown,
            'adjustments': adjustments,
            'total_nights': nights,
            'final_total': self.calculate_cost()
        }

    @property
    def is_editable(self):
        return self.status == 'Draft'  # Only allow editing for Draft status

    def save(self, *args, **kwargs):
        # Check if this is a new instance or if application_status has changed to 'Onboarding'
        if self.pk:
            old_instance = Application.objects.get(pk=self.pk)
            if old_instance.application_status != 'Onboarding' and self.application_status == 'Onboarding':
                # Create chapter booking when status changes to Onboarding
                if self.chapter and self.date_join and self.date_leave:
                    ChapterBooking.objects.create(
                        chapter=self.chapter,
                        start_date=self.date_join,
                        end_date=self.date_leave
                    )
        
        super().save(*args, **kwargs)

    def withdraw(self):
        """Withdraw the application."""
        self.status = 'Withdrawn'
        self.application_status = 'Withdrawn'
        self.save()

    def __str__(self):
        return f"{self.first_name} {self.last_name}'s Application"


class ActiveApplication(Application):
    class Meta:
        proxy = True
        verbose_name = 'Active Application'
        verbose_name_plural = 'Active Applications'


class ArchivedApplication(Application):
    class Meta:
        proxy = True
        verbose_name = 'Archived Application'
        verbose_name_plural = 'Archived Applications'


class ApplicationAnswer(models.Model):
    application = models.ForeignKey(Application, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['application', 'question']
        ordering = ['question__order']

    def __str__(self):
        return f"Answer to {self.question} for {self.application}"


class ReintroductionAnswer(models.Model):
    application = models.ForeignKey(Application, related_name='reintroduction_answers', on_delete=models.CASCADE)
    question = models.ForeignKey('questions.ReintroductionQuestion', related_name='answers', on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['application', 'question']
        ordering = ['question__order']

    def __str__(self):
        return f"Reintroduction answer to {self.question} for {self.application}"


class ReintroductionQuestionSettings(models.Model):
    title = models.CharField(max_length=200, default="Welcome Back!")
    subtitle = models.CharField(max_length=200, default="We're excited to have you apply again.")
    question_text = models.CharField(max_length=300, default="Would you like to reintroduce yourself?")
    description = models.TextField(default="As a returning member, you have the option to share an updated introduction with the community. This is completely optional - you can choose to skip this step and submit your application directly.")
    yes_option_title = models.CharField(max_length=100, default="Yes, I'd like to reintroduce myself")
    yes_option_description = models.CharField(max_length=200, default="Complete the reintroduction form and submit your application")
    no_option_title = models.CharField(max_length=100, default="No, skip the reintroduction")
    no_option_description = models.CharField(max_length=200, default="Submit your application without reintroducing yourself")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Reintroduction Question Settings"
        verbose_name_plural = "Reintroduction Question Settings"

    def save(self, *args, **kwargs):
        # Ensure only one active setting exists
        if self.is_active:
            ReintroductionQuestionSettings.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            # Return default settings if none exists
            return cls(
                title="Welcome Back!",
                subtitle="We're excited to have you apply again.",
                question_text="Would you like to reintroduce yourself?",
                description="As a returning member, you have the option to share an updated introduction with the community. This is completely optional - you can choose to skip this step and submit your application directly.",
                yes_option_title="Yes, I'd like to reintroduce myself",
                yes_option_description="Complete the reintroduction form and submit your application",
                no_option_title="No, skip the reintroduction",
                no_option_description="Submit your application without reintroducing yourself"
            )


class ShortStayWarning(models.Model):
    title = models.CharField(max_length=200, default="Stay Duration Notice")
    message = models.TextField(default="Please note that we prioritize stays over 1 month. While shorter stays are possible, longer-term residents will be given priority in the application process.")
    button_text = models.CharField(max_length=50, default="I understand, continue anyway")
    minimum_days = models.PositiveIntegerField(default=28, help_text="Minimum number of days before showing the short stay warning")
    
    # Upper bound fields
    maximum_days = models.PositiveIntegerField(default=93, help_text="Maximum number of days before showing the long stay warning")
    long_stay_title = models.CharField(max_length=200, default="Extended Stay Notice")
    long_stay_message = models.TextField(default="Please note that initial bookings are limited to 3 months. You can extend your stay after arrival if space is available.")
    long_stay_button_text = models.CharField(max_length=50, default="I understand, continue anyway")
    
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Short Stay Warning Message"
        verbose_name_plural = "Short Stay Warning Message"

    def save(self, *args, **kwargs):
        # Ensure only one active warning exists
        if self.is_active:
            ShortStayWarning.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            # Return default message if none exists
            return cls(
                title="Stay Duration Notice",
                message="Please note that we prioritize stays over 1 month. While shorter stays are possible, longer-term residents will be given priority in the application process.",
                button_text="I understand, continue anyway",
                minimum_days=28,
                maximum_days=93,
                long_stay_title="Extended Stay Notice",
                long_stay_message="Please note that initial bookings are limited to 3 months. You can extend your stay after arrival if space is available.",
                long_stay_button_text="I understand, continue anyway"
            )
    
    