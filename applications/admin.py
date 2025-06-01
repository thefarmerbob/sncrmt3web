from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from .models import Application, ApplicationAnswer, ReintroductionAnswer, ActiveApplication, ArchivedApplication, ShortStayWarning, PricingSettings, ReintroductionQuestionSettings

@admin.register(ReintroductionQuestionSettings)
class ReintroductionQuestionSettingsAdmin(admin.ModelAdmin):
    list_display = ('title', 'question_text', 'is_active')
    fieldsets = (
        ('Header Text', {
            'fields': ('title', 'subtitle'),
            'description': 'The main title and subtitle shown at the top of the reintroduction question page.'
        }),
        ('Question Content', {
            'fields': ('question_text', 'description'),
            'description': 'The main question and explanatory text.'
        }),
        ('Yes Option', {
            'fields': ('yes_option_title', 'yes_option_description'),
            'description': 'Text for the "Yes" option when users want to reintroduce themselves.'
        }),
        ('No Option', {
            'fields': ('no_option_title', 'no_option_description'),
            'description': 'Text for the "No" option when users want to skip reintroduction.'
        }),
        ('Settings', {
            'fields': ('is_active',),
        }),
    )

    def has_add_permission(self, request):
        # Prevent creating multiple instances
        return not ReintroductionQuestionSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the only instance
        return False

@admin.register(ShortStayWarning)
class ShortStayWarningAdmin(admin.ModelAdmin):
    list_display = ('title', 'minimum_days', 'maximum_days', 'is_active')
    fieldsets = (
        ('Short Stay Warning (Lower Bound)', {
            'fields': ('title', 'message', 'button_text', 'minimum_days'),
            'description': 'Settings for warning users about stays that are too short.'
        }),
        ('Long Stay Warning (Upper Bound)', {
            'fields': ('long_stay_title', 'long_stay_message', 'long_stay_button_text', 'maximum_days'),
            'description': 'Settings for warning users about stays that are too long.'
        }),
        ('General Settings', {
            'fields': ('is_active',),
        }),
    )

@admin.register(PricingSettings)
class PricingSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Pricing Rules', {
            'fields': ('member_discount', 'guest_increase'),
            'description': 'Configure the percentage values for member discounts and guest increases.'
        }),
        ('Display Text', {
            'fields': ('pricing_info_title', 'base_price_text', 'member_discount_text', 'guest_increase_text', 'calculation_note'),
            'description': 'Customize the text shown in the pricing information modal. Use {discount} and {increase} placeholders to insert the actual percentage values.'
        }),
    )

    def has_add_permission(self, request):
        # Prevent creating multiple instances
        return not PricingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the only instance
        return False

def export_to_pdf(modeladmin, request, queryset):
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="applications.pdf"'
    
    # Create the PDF object using ReportLab
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # Add title
    elements.append(Paragraph('Applications Report', title_style))
    elements.append(Spacer(1, 12))
    
    # Create table data
    data = [['Name', 'Email', 'Chapter', 'Status', 'Total Cost']]
    for app in queryset:
        data.append([
            f"{app.first_name} {app.last_name}",
            app.email,
            str(app.chapter) if app.chapter else 'N/A',
            app.application_status,
            app.total_cost
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    return response

export_to_pdf.short_description = "Export selected applications to PDF"

class ApplicationAnswerInline(admin.TabularInline):
    model = ApplicationAnswer
    extra = 0
    readonly_fields = ('question', 'answer')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False

class ReintroductionAnswerInline(admin.TabularInline):
    model = ReintroductionAnswer
    extra = 0
    readonly_fields = ('question', 'answer')
    can_delete = False
    max_num = 0
    verbose_name = "Reintroduction Answer"
    verbose_name_plural = "Reintroduction Answers"
    
    def has_add_permission(self, request, obj=None):
        return False

class BaseApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'chapter', 'created_at', 'status', 'application_status', 'total_cost', 'manual_cost_display')
    list_filter = ('status', 'application_status', 'chapter', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')
    readonly_fields = ('created_by', 'created_at', 'modified_at', 'total_cost', 'wants_reintroduction', 'reintroduction_completed')
    inlines = [ApplicationAnswerInline, ReintroductionAnswerInline]
    actions = [export_to_pdf]

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'

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
            'fields': (('date_join', 'date_leave'), 'guests', 'member_type', 'chapter')
        }),
        ('Cost Information', {
            'fields': ('total_cost', 'manual_cost'),
            'description': 'The total cost is automatic based on stay duration and other factors. Use manual cost to override if needed.'
        }),
        ('Status Information', {
            'fields': ('status', 'application_status', 'is_active')
        }),
        ('Reintroduction Information', {
            'fields': ('wants_reintroduction', 'reintroduction_completed'),
            'classes': ('collapse',),
            'description': 'Information about whether the returning member chose to reintroduce themselves.'
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )

class ActiveApplicationAdmin(BaseApplicationAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_active=True)

    def save_model(self, request, obj, form, change):
        if not obj.is_active:
            # If is_active was unchecked, save it as False
            super().save_model(request, obj, form, change)
        else:
            # Only force is_active=True if it was checked
            obj.is_active = True
            super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        # If the object is no longer active, redirect to the archived applications
        if not obj.is_active:
            from django.contrib import messages
            pass  # Application moved to archive silently
        return super().response_change(request, obj)

class ArchivedApplicationAdmin(BaseApplicationAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_active=False)

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            # If is_active was checked, save it as True
            super().save_model(request, obj, form, change)
        else:
            # Only force is_active=False if it was unchecked
            obj.is_active = False
            super().save_model(request, obj, form, change)

# Register the active and archived applications separately
admin.site.register(ActiveApplication, ActiveApplicationAdmin)
admin.site.register(ArchivedApplication, ArchivedApplicationAdmin)