from django.db import models
from django.core.exceptions import ValidationError

class SiteSettings(models.Model):
    logo = models.ImageField(upload_to='site_settings/', null=True, blank=True)
    favicon = models.ImageField(upload_to='site_settings/', null=True, blank=True, help_text='Small square image (32x32 or 16x16 pixels) for the browser tab')
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def save(self, *args, **kwargs):
        if SiteSettings.objects.exists() and not self.pk:
            raise ValidationError('There can only be one SiteSettings instance')
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        return cls.objects.first()
