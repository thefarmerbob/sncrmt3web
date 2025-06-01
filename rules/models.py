from django.db import models
from django.utils import timezone
from chapters.models import Chapter

class Rule(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    chapters = models.ManyToManyField(Chapter, related_name='rules', blank=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title
