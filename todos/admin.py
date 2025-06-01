from django.contrib import admin
from django.utils import timezone
from .models import Todo, CompletedTodo

class BaseTodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_name', 'task_type', 'status', 'due_date', 'created_at')
    list_filter = ('task_type', 'status')
    search_fields = ('title', 'description', 'reference_id', 'coliver_name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'task_type', 'coliver_name')
        }),
        ('Status & Due Date', {
            'fields': ('status', 'due_date')
        }),
        ('Reference', {
            'fields': ('reference_id',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'created_by')
    
    def get_name(self, obj):
        return obj.coliver_name
    get_name.short_description = 'Name'
    get_name.admin_order_field = 'coliver_name'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Todo)
class TodoAdmin(BaseTodoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='pending')
    
    actions = ['mark_completed']
    
    def mark_completed(self, request, queryset):
        for todo in queryset:
            todo.mark_as_completed()
    mark_completed.short_description = "Mark selected tasks as completed"

@admin.register(CompletedTodo)
class CompletedTodoAdmin(BaseTodoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='completed')
    
    list_editable = ()  # Remove editable fields for completed todos
    readonly_fields = BaseTodoAdmin.readonly_fields + ('status', 'due_date', 'title', 'description', 'task_type', 'coliver_name')

    def has_add_permission(self, request):
        return False  # Prevent adding completed todos directly
