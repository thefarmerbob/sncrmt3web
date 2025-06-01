from django.contrib import admin
from .models import ChapterTransferRequest, TransferAcknowledgmentText

@admin.register(TransferAcknowledgmentText)
class TransferAcknowledgmentTextAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'is_active', 'updated_at']
    list_filter = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('text', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def text_preview(self, obj):
        return f"{obj.text[:100]}..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Text'

@admin.register(ChapterTransferRequest)
class ChapterTransferRequestAdmin(admin.ModelAdmin):
    list_display = ['coliver', 'current_chapter', 'requested_chapter', 'start_date', 'status', 'acknowledgment']
    list_filter = ['status', 'current_chapter', 'requested_chapter', 'acknowledgment']
    search_fields = ['coliver__username', 'coliver__email', 'reason', 'admin_notes']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('coliver', 'status')
        }),
        ('Chapter Information', {
            'fields': ('current_chapter', 'requested_chapter', 'start_date')
        }),
        ('Request Details', {
            'fields': ('reason', 'acknowledgment', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # You could add additional logic here when status changes
            pass
        super().save_model(request, obj, form, change)
