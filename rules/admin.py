from django.contrib import admin
from .models import Rule

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_chapters', 'is_active', 'order', 'created_at', 'updated_at')
    list_filter = ('is_active', 'chapters')
    search_fields = ('title', 'description')
    ordering = ('order', '-created_at')
    list_editable = ('is_active', 'order')
    filter_horizontal = ('chapters',)  # Makes it easier to select multiple chapters
    
    def get_chapters(self, obj):
        return ", ".join([chapter.name for chapter in obj.chapters.all()]) or "All chapters"
    get_chapters.short_description = 'Chapters'
