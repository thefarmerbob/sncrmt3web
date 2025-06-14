from django.contrib import admin

# Register your models here.
from .models import Chapter, ChapterBooking, ChapterImage, PricingTier

class ChapterBookingsInline(admin.TabularInline):
    model = ChapterBooking
    extra = 1

class ChapterImageInline(admin.TabularInline):
    model = ChapterImage
    extra = 1  # Number of empty forms to display

class PricingTierInline(admin.TabularInline):
    model = PricingTier
    extra = 1
    fields = ('tier_name', 'duration_days', 'price_per_night', 'tier_order')
    ordering = ['tier_order']

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['name', 'cost_per_night', 'use_tiered_pricing', 'use_short_term_pricing', 'description_text_size', 'created_by']
    list_filter = ['use_tiered_pricing', 'use_short_term_pricing', 'created_by']
    search_fields = ['name']
    inlines = [PricingTierInline, ChapterBookingsInline, ChapterImageInline]
    exclude = ('created_by',)  # Exclude from form since it's set automatically
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'description_text_size')
        }),
        ('Pricing Configuration', {
            'fields': ('use_tiered_pricing', 'cost_per_night'),
            'description': 'Enable tiered pricing to set different rates based on length of stay. '
                          'When tiered pricing is disabled, the legacy cost_per_night will be used.'
        }),
        ('Short-term Stay Pricing', {
            'fields': ('use_short_term_pricing', 'short_term_threshold_days', 'short_term_price_per_night'),
            'description': 'Enable special pricing for very short stays. This takes priority over tiered pricing '
                          'when the stay duration is under the threshold.'
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ['chapter', 'tier_name', 'duration_days', 'price_per_night', 'tier_order']
    list_filter = ['chapter']
    search_fields = ['chapter__name', 'tier_name']
    ordering = ['chapter', 'tier_order']
