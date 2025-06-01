from django.db import models
from decimal import Decimal

class Archive(models.Model):


    APPLICATION_STATUS_CHOICES = [
        ('Approved for interview', 'Approved for interview'),
        ('Scheduled interview', 'Scheduled interview'),
        ('Interview passed', 'Interview passed'),
        ('Rejected', 'Rejected'),
        ('Accepted', 'Accepted'),
        ('Waiting list', 'Waiting list'),
        ('Application in progress', 'Application in progress'),
        ('Submitted', 'Submitted'),
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

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    date_join = models.DateField(verbose_name='Arrival Date', null=True, blank=True)
    date_leave = models.DateField(verbose_name='Departure Date', null=True, blank=True)
    member_type = models.CharField(max_length=20, choices=MEMBER_TYPE_CHOICES, default='new member')
    guests = models.CharField(max_length=2, choices=GUESTS_CHOICES, default='1')
    application_status = models.CharField(max_length=40, choices=APPLICATION_STATUS_CHOICES, default='Application in progress')
    chapter = models.ForeignKey('chapters.Chapter', on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_applications')
    application_answers = models.ManyToManyField('applications.ApplicationAnswer', related_name='archive_application_answers')
    manual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Override the automatically calculated cost. Leave empty to use calculated cost.")
    
    def calculate_cost(self):
        """Calculate the total cost for the archived application using tiered pricing."""
        if self.manual_cost is not None:
            return self.manual_cost
            
        if self.chapter and self.date_join and self.date_leave:
            nights = (self.date_leave - self.date_join).days
            # Use tiered pricing if enabled, otherwise fall back to legacy pricing
            base_cost = self.chapter.calculate_tiered_cost(nights)
            
            # Apply 3% discount for returning members (using hardcoded values for archived data)
            if self.member_type == 'returning member':
                base_cost = base_cost * Decimal('0.97')
            
            # Apply 20% increase for 2 guests
            if self.guests == '2':
                base_cost = base_cost * Decimal('1.20')
            
            return round(base_cost, 2)
        return Decimal('0.00')

    @property
    def total_cost(self):
        """Return the formatted total cost with Korean Won sign and commas."""
        return f"₩{self.calculate_cost():,.2f}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}'s Archived Application"
    
