from django.db import models

# Create your models here.

class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Text Answer'),
        ('multiple_choice', 'Multiple Choice'),
        ('information', 'Information Display')
    ]
    
    text = models.TextField(verbose_name="Question Text")
    description = models.TextField(verbose_name="Question Description", blank=True, help_text="Additional explanatory text for the question")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='text', help_text="Type of question (text or multiple choice)")
    choices = models.JSONField(null=True, blank=True, help_text="List of choices for multiple choice questions. Format: [{'text': 'Choice 1'}, {'text': 'Choice 2'}]")
    order = models.PositiveIntegerField(default=0, help_text="Order in which the question appears in the form")
    is_active = models.BooleanField(default=True, help_text="Whether this question is currently active and should be shown in the form")
    required = models.BooleanField(default=True, help_text="Whether this question is required to be answered")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Question {self.order}: {self.text[:50]}..."


class ReintroductionQuestion(models.Model):
    QUESTION_TYPES = [
        ('text', 'Text Answer'),
        ('multiple_choice', 'Multiple Choice'),
        ('information', 'Information Display')
    ]
    
    text = models.TextField(verbose_name="Question Text")
    description = models.TextField(verbose_name="Question Description", blank=True, help_text="Additional explanatory text for the question")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='text', help_text="Type of question (text or multiple choice)")
    choices = models.JSONField(null=True, blank=True, help_text="List of choices for multiple choice questions. Format: [{'text': 'Choice 1'}, {'text': 'Choice 2'}]")
    order = models.PositiveIntegerField(default=0, help_text="Order in which the question appears in the reintroduction form")
    is_active = models.BooleanField(default=True, help_text="Whether this question is currently active and should be shown in the reintroduction form")
    required = models.BooleanField(default=True, help_text="Whether this question is required to be answered")

    class Meta:
        ordering = ['order']
        verbose_name = "Reintroduction Question"
        verbose_name_plural = "Reintroduction Questions"

    def __str__(self):
        return f"Reintroduction Question {self.order}: {self.text[:50]}..."
