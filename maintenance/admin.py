from django.contrib import admin
from .models import MaintenanceRequest, MaintenanceConfirmationText
from django.utils import timezone

@admin.register(MaintenanceConfirmationText)
class MaintenanceConfirmationTextAdmin(admin.ModelAdmin):
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

class PendingMaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description', 'created_by__username', 'created_by__first_name', 'created_by__last_name']
    readonly_fields = ['created_by', 'created_at', 'user_confirmation']
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'created_by', 'created_at')
        }),
        ('Status & Notes', {
            'fields': ('status', 'manager_notes')
        }),
        ('User Confirmation', {
            'fields': ('user_confirmation',),
            'description': 'User has confirmed this maintenance request'
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='pending')
    
    def has_delete_permission(self, request, obj=None):
        return True

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new object
            obj.created_by = request.user
        if obj.status == 'completed' and not obj.completed_at:
            obj.completed_at = timezone.now()
        super().save_model(request, obj, form, change)

class CompletedMaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['title', 'description', 'created_by__username', 'created_by__first_name', 'created_by__last_name']
    readonly_fields = ['created_by', 'created_at', 'completed_at', 'title', 'description', 'user_confirmation']
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'created_by', 'created_at')
        }),
        ('Completion', {
            'fields': ('completed_at', 'manager_notes')
        }),
        ('User Confirmation', {
            'fields': ('user_confirmation',),
            'description': 'User has confirmed this maintenance request'
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='completed')
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# Register the same model with two different admin classes
admin.site.register(MaintenanceRequest, PendingMaintenanceRequestAdmin)

# Use a proxy model for the completed requests to show them in a separate tab
class CompletedMaintenanceRequest(MaintenanceRequest):
    class Meta:
        proxy = True
        verbose_name = 'Completed maintenance request'
        verbose_name_plural = 'Completed maintenance requests'

admin.site.register(CompletedMaintenanceRequest, CompletedMaintenanceRequestAdmin)
