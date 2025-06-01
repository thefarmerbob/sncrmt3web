from django.contrib import admin
from .models import Question, ReintroductionQuestion

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_type', 'description', 'order', 'is_active', 'required')
    list_filter = ('is_active', 'question_type', 'required')
    search_fields = ('text', 'description')
    ordering = ('order',)
    fieldsets = (
        (None, {
            'fields': ('text', 'description', 'order', 'is_active', 'required')
        }),
        ('Question Type', {
            'fields': ('question_type', 'choices'),
            'description': 'For multiple choice questions, enter choices as a JSON array of objects with "text" keys. Example: [{"text": "Choice 1"}, {"text": "Choice 2"}]'
        }),
    )


@admin.register(ReintroductionQuestion)
class ReintroductionQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_type', 'description', 'order', 'is_active', 'required')
    list_filter = ('is_active', 'question_type', 'required')
    search_fields = ('text', 'description')
    ordering = ('order',)
    fieldsets = (
        (None, {
            'fields': ('text', 'description', 'order', 'is_active', 'required')
        }),
        ('Question Type', {
            'fields': ('question_type', 'choices'),
            'description': 'For multiple choice questions, enter choices as a JSON array of objects with "text" keys. Example: [{"text": "Choice 1"}, {"text": "Choice 2"}]'
        }),
    )
