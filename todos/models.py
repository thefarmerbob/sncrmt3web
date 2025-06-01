from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Todo(models.Model):
    TASK_TYPES = [
        ('application_review', 'Application Review'),
        ('payment_review', 'Payment Review'),
        ('transfer_review', 'Transfer Review'),
        ('maintenance_review', 'Maintenance Review'),
        ('maintenance_verification', 'Maintenance Verification'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_todos')
    reference_id = models.CharField(max_length=100, null=True, blank=True, help_text='ID of the related application/payment')
    coliver_name = models.CharField(max_length=255, null=True, blank=True, help_text='Name of the person associated with this task')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Todo'
        verbose_name_plural = 'Todos'

    def __str__(self):
        return self.title

    def mark_as_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

class CompletedTodo(Todo):
    class Meta:
        proxy = True
        verbose_name = 'Completed Todo'
        verbose_name_plural = 'Completed Todos'
