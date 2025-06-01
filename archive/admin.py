from django.contrib import admin
from django.utils.html import format_html_join, format_html
from django.utils.safestring import mark_safe

# Register your models here.
from .models import Archive

@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'date_join', 'date_leave', 'member_type', 'guests', 'application_status', 'chapter', 'total_cost', 'manual_cost_display')
    list_filter = ('application_status', 'member_type', 'guests', 'chapter')
    search_fields = ('first_name', 'last_name', 'email')
    
    def formatted_application_answers(self, obj):
        if not obj.application_answers.exists():
            return "-"
        
        answers_html = format_html_join(
            mark_safe('<br><br>'),
            """
            <div style="margin-bottom: 10px;">
                <strong>Question {}: {}</strong><br>
                Answer: {}
            </div>
            """,
            (
                (
                    i + 1,
                    answer.question,
                    answer.answer or "-"
                )
                for i, answer in enumerate(obj.application_answers.all())
            )
        )
        return format_html('<div style="max-width: 800px;">{}</div>', answers_html)
    
    formatted_application_answers.short_description = "Application Answers"
    
    readonly_fields = ('total_cost', 'formatted_application_answers')

    def manual_cost_display(self, obj):
        if obj.manual_cost is not None:
            return f"₩{obj.manual_cost:,.2f}"
        return "-"
    manual_cost_display.short_description = 'Manual Cost'

    fieldsets = (
        ('Personal Information', {
            'fields': (('first_name', 'last_name'), 'email')
        }),
        ('Stay Details', {
            'fields': (('date_join', 'date_leave'), 'member_type', 'guests', 'chapter')
        }),
        ('Cost Information', {
            'fields': ('total_cost', 'manual_cost'),
            'description': 'The total cost is calculated based on stay duration and other factors. Use manual cost to override if needed.'
        }),
        ('Status Information', {
            'fields': ('application_status',)
        }),
        ('Application Details', {
            'fields': ('formatted_application_answers',),
            'classes': ('collapse',)
        })
    )
