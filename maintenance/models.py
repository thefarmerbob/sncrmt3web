from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from todos.models import Todo

class MaintenanceConfirmationText(models.Model):
    text = models.TextField(
        default="I confirm that this maintenance request is accurate and needs attention",
        help_text="This text will appear above the confirmation checkbox when users submit maintenance requests"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Maintenance Confirmation Text"
        verbose_name_plural = "Maintenance Confirmation Texts"

    def __str__(self):
        return f"{self.text[:50]}..." if len(self.text) > 50 else self.text

    def save(self, *args, **kwargs):
        if self.is_active:
            # Set all other texts to inactive
            MaintenanceConfirmationText.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_requests')
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    manager_notes = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    user_confirmation = models.BooleanField(
        default=False,
        verbose_name="User Confirmation",
        help_text="Required confirmation from the user"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.created_by.username}"
