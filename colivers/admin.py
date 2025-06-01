from django.contrib import admin
from .models import Coliver

# Create proxy models for active and archived colivers
class ActiveColiver(Coliver):
    class Meta:
        proxy = True
        verbose_name = 'Active Coliver'
        verbose_name_plural = 'Active Colivers'

class ArchivedColiver(Coliver):
    class Meta:
        proxy = True
        verbose_name = 'Archived Coliver'
        verbose_name_plural = 'Archived Colivers'

class BaseColiverAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'arrival_date', 'departure_date', 'created_at', 'total_cost', 'manual_cost_display', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = ['is_active', 'arrival_date', 'departure_date', 'status']
    readonly_fields = ['created_at', 'total_cost']

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
            'fields': (('arrival_date', 'departure_date'), 'chapter_name')
        }),
        ('Cost Information', {
            'fields': ('total_cost', 'manual_cost'),
            'description': 'The total cost is automatic based on stay duration and chapter rates. Use manual cost to override if needed.'
        }),
        ('Status Information', {
            'fields': ('status', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

class ActiveColiverAdmin(BaseColiverAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_active=True)

class ArchivedColiverAdmin(BaseColiverAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_active=False)

# Register the active and archived colivers separately
admin.site.register(ActiveColiver, ActiveColiverAdmin)
admin.site.register(ArchivedColiver, ArchivedColiverAdmin)
