from django.db import models
from django.contrib.auth.models import User
from chapters.models import Chapter

# Create your models here.

class TransferAcknowledgmentText(models.Model):
    text = models.TextField(
        default="I acknowledge that if there is currently another coliver residing in this chapter, "
        "I have communicated with them about switching rooms, and that they also have filled out this form"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transfer Acknowledgment Text"
        verbose_name_plural = "Transfer Acknowledgment Text"

    def save(self, *args, **kwargs):
        # Ensure only one active text at a time
        if self.is_active:
            TransferAcknowledgmentText.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Acknowledgment Text {'(Active)' if self.is_active else ''}"

class ChapterTransferRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    coliver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chapter_transfer_requests')
    current_chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='transfer_requests_from')
    requested_chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='transfer_requests_to')
    start_date = models.DateField(help_text="When they want to start at the new chapter", null=True)
    end_date = models.DateField(help_text="When they will end their stay at the current chapter", null=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledgment = models.BooleanField(default=False, help_text="User has acknowledged the transfer conditions")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.coliver.username}'s request to transfer from {self.current_chapter} to {self.requested_chapter}"
