from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from todos.models import Todo
from django.utils import timezone

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('requested', 'Payment Requested'),
        ('proof_submitted', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Archived'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='requested')
    payment_method = models.CharField(max_length=100, null=True, blank=True, help_text="Enter the payment method you used (e.g. Revolut, Bank Transfer)")
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    rejection_note = models.TextField(blank=True, help_text="Reason for rejecting the payment proof")
    user_notes = models.TextField(blank=True, help_text="Any additional notes or comments about this payment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_payments')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} - {self.amount} ({self.status})"

    def get_absolute_url(self):
        return reverse('payments:payment_detail', args=[str(self.id)])

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date and timezone.now().date() > self.due_date

    def complete_associated_todo(self):
        """Complete any todo items associated with this payment when it's approved"""
        if self.status == 'approved':
            todos = Todo.objects.filter(
                task_type='payment_review',
                reference_id=str(self.id),
                status='pending'
            )
            for todo in todos:
                todo.mark_as_completed()

    def save(self, *args, **kwargs):
        # Check if status is being changed to approved
        if self.pk:  # If this is an existing object
            old_payment = Payment.objects.get(pk=self.pk)
            if old_payment.status != 'approved' and self.status == 'approved':
                self.complete_associated_todo()
        super().save(*args, **kwargs)


class AutomaticPaymentTemplate(models.Model):
    """Template for automatic payments that get created for colivers"""
    DATE_TYPE_CHOICES = [
        ('arrival_date', 'Arrival Date'),
        ('departure_date', 'Departure Date'),
        ('custom_offset', 'Custom Days After Arrival'),
    ]
    
    AMOUNT_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('total_cost', 'Total Stay Cost'),
        ('percentage_cost', 'Percentage of Total Cost'),
    ]

    title = models.CharField(max_length=255, help_text="Title for this automatic payment (e.g., 'Booking Payment', 'Security Deposit')")
    description_template = models.CharField(max_length=500, help_text="Description template - use {coliver_name}, {chapter_name}, {arrival_date}, {departure_date}")
    
    # Date configuration
    date_type = models.CharField(max_length=20, choices=DATE_TYPE_CHOICES, default='arrival_date')
    days_offset = models.IntegerField(default=0, help_text="Days to add/subtract from the base date (negative for before, positive for after)")
    
    # Amount configuration
    amount_type = models.CharField(max_length=20, choices=AMOUNT_TYPE_CHOICES, default='total_cost')
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Fixed amount (only used if amount_type is 'fixed')")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Percentage of total cost (only used if amount_type is 'percentage_cost')")
    
    # Settings
    is_active = models.BooleanField(default=True, help_text="Whether this template is active and should create payments")
    applies_to_all_colivers = models.BooleanField(default=True, help_text="Whether this payment applies to all colivers")
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_payment_templates')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_amount_type_display()})"
    
    def calculate_amount(self, coliver):
        """Calculate the payment amount based on the template configuration"""
        if self.amount_type == 'fixed':
            return self.fixed_amount or 0
        elif self.amount_type == 'total_cost':
            return coliver.calculate_cost()
        elif self.amount_type == 'percentage_cost':
            return coliver.calculate_cost() * (self.percentage / 100) if self.percentage else 0
        return 0
    
    def calculate_due_date(self, coliver):
        """Calculate the due date based on the template configuration"""
        if self.date_type == 'arrival_date':
            base_date = coliver.arrival_date
        elif self.date_type == 'departure_date':
            base_date = coliver.departure_date
        else:  # custom_offset
            base_date = coliver.arrival_date
        
        if base_date:
            return base_date + timezone.timedelta(days=self.days_offset)
        return None
    
    def create_payment_for_coliver(self, coliver, created_by=None):
        """Create an automatic payment for a specific coliver based on this template"""
        from colivers.models import Coliver
        
        if not self.is_active:
            return None
            
        # Check if payment already exists
        existing_payment = AutomaticPayment.objects.filter(
            template=self,
            coliver=coliver
        ).first()
        
        if existing_payment:
            return existing_payment.payment
        
        # Calculate amount and due date
        amount = self.calculate_amount(coliver)
        due_date = self.calculate_due_date(coliver)
        
        # Format description
        description = self.description_template.format(
            coliver_name=f"{coliver.first_name} {coliver.last_name}",
            chapter_name=coliver.chapter_name.name if coliver.chapter_name else "No Chapter",
            arrival_date=coliver.arrival_date.strftime('%Y-%m-%d') if coliver.arrival_date else "TBD",
            departure_date=coliver.departure_date.strftime('%Y-%m-%d') if coliver.departure_date else "TBD"
        )
        
        # Create the payment
        payment = Payment.objects.create(
            user=coliver.user,
            amount=amount,
            description=description,
            due_date=due_date,
            created_by=created_by
        )
        
        # Create the automatic payment record
        AutomaticPayment.objects.create(
            template=self,
            coliver=coliver,
            payment=payment,
            created_by=created_by
        )
        
        return payment


class AutomaticPayment(models.Model):
    """Tracks automatic payments created from templates for specific colivers"""
    template = models.ForeignKey(AutomaticPaymentTemplate, on_delete=models.CASCADE, related_name='automatic_payments')
    coliver = models.ForeignKey('colivers.Coliver', on_delete=models.CASCADE, related_name='automatic_payments')
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='automatic_payment')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_automatic_payments')

    class Meta:
        unique_together = ['template', 'coliver']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.template.title} for {self.coliver.first_name} {self.coliver.last_name}"
