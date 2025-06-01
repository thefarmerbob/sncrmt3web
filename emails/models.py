from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class EmailTemplate(models.Model):
    name = models.CharField(max_length=255, help_text="Template name for identification")
    subject = models.CharField(max_length=255, help_text="Email subject line")
    body = models.TextField(help_text="Email body content. You can use placeholders like {{first_name}}, {{last_name}}, {{email}}")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether this template is available for use")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RecurringEmail(models.Model):
    RECIPIENT_CHOICES = [
        ('applicants', 'Applicants'),
        ('colivers', 'Colivers'),
        ('both', 'Both Applicants and Colivers'),
    ]
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    name = models.CharField(max_length=255, help_text="Name for this recurring email setup")
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='recurring_emails')
    recipients = models.CharField(max_length=20, choices=RECIPIENT_CHOICES, default='both')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    next_send_date = models.DateTimeField(help_text="When this email should be sent next")
    is_active = models.BooleanField(default=True, help_text="Whether this recurring email is active")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_emails')
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent = models.DateTimeField(null=True, blank=True, help_text="When this was last sent")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='email_logs')
    recurring_email = models.ForeignKey(RecurringEmail, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=255, blank=True)
    recipient_type = models.CharField(max_length=20, choices=[
        ('applicant', 'Applicant'),
        ('coliver', 'Coliver'),
    ])
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_emails')
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Email to {self.recipient_email} - {self.subject}"
