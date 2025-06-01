from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, AutomaticPaymentTemplate, AutomaticPayment
from colivers.models import Coliver
from django.contrib.auth.models import User
from django import forms
from django.db.models import Q
from django.utils import timezone
from django.db import models

# Create a proxy model for archived payments
class ArchivedPayment(Payment):
    class Meta:
        proxy = True
        verbose_name = 'Archived Payment'
        verbose_name_plural = 'Archived Payments'

class PriceRangeFilter(admin.SimpleListFilter):
    title = 'Price Range'
    parameter_name = 'amount_range'

    def lookups(self, request, model_admin):
        return (
            ('0-100', '€0 - €100'),
            ('100-500', '€100 - €500'),
            ('500-1000', '€500 - €1000'),
            ('1000+', '€1000+'),
        )

    def queryset(self, request, queryset):
        if self.value() == '0-100':
            return queryset.filter(amount__lte=100)
        if self.value() == '100-500':
            return queryset.filter(amount__gt=100, amount__lte=500)
        if self.value() == '500-1000':
            return queryset.filter(amount__gt=500, amount__lte=1000)
        if self.value() == '1000+':
            return queryset.filter(amount__gt=1000)

class ColiverFilter(admin.SimpleListFilter):
    title = 'Coliver'
    parameter_name = 'coliver'

    def lookups(self, request, model_admin):
        colivers = Coliver.objects.all().order_by('first_name', 'last_name')
        return [(c.id, f"{c.first_name} {c.last_name} ({c.chapter_name.name if c.chapter_name else 'No Chapter'})") for c in colivers]

    def queryset(self, request, queryset):
        if self.value():
            try:
                coliver = Coliver.objects.get(id=self.value())
                return queryset.filter(user=coliver.user)
            except Coliver.DoesNotExist:
                return queryset.none()

class DueDateStatusFilter(admin.SimpleListFilter):
    title = 'Due Date Status'
    parameter_name = 'due_date_status'

    def lookups(self, request, model_admin):
        return (
            ('overdue', 'Overdue'),
            ('due_today', 'Due Today'),
            ('due_this_week', 'Due This Week'),
            ('due_next_week', 'Due Next Week'),
            ('future', 'Future'),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'overdue':
            return queryset.filter(due_date__lt=today)
        if self.value() == 'due_today':
            return queryset.filter(due_date=today)
        if self.value() == 'due_this_week':
            week_end = today + timezone.timedelta(days=(6-today.weekday()))
            return queryset.filter(due_date__gt=today, due_date__lte=week_end)
        if self.value() == 'due_next_week':
            next_week_start = today + timezone.timedelta(days=(7-today.weekday()))
            next_week_end = next_week_start + timezone.timedelta(days=6)
            return queryset.filter(due_date__gt=next_week_start, due_date__lte=next_week_end)
        if self.value() == 'future':
            return queryset.filter(due_date__gt=today + timezone.timedelta(days=14))

class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update the user field to show more information
        def user_label(obj):
            try:
                # Try to get the coliver info for this user
                coliver = Coliver.objects.filter(user=obj).order_by('-created_at').first()
                if coliver:
                    chapter_name = coliver.chapter_name.name if coliver.chapter_name else 'No Chapter'
                    return f"{coliver.first_name} {coliver.last_name} ({chapter_name}) - {obj.username}"
                else:
                    return f"{obj.username} (No coliver profile)"
            except:
                return f"{obj.username}"
        
        self.fields['user'].label_from_instance = user_label
        self.fields['user'].queryset = User.objects.filter(
            id__in=Coliver.objects.values_list('user_id', flat=True)
        ).order_by('username')
        self.fields['user'].empty_label = "Select a user..."

    def clean_transaction_id(self):
        transaction_id = self.cleaned_data.get('transaction_id')
        if transaction_id == '':
            return None
        
        if transaction_id:
            # Check for existing transaction IDs
            existing_query = Payment.objects.filter(transaction_id=transaction_id)
            if self.instance.pk:
                existing_query = existing_query.exclude(pk=self.instance.pk)
            
            if existing_query.exists():
                raise forms.ValidationError(f"A payment with transaction ID '{transaction_id}' already exists.")
        
        return transaction_id

class BasePaymentAdmin(admin.ModelAdmin):
    """Base admin class with common functionality for both active and archived payments"""
    form = PaymentAdminForm
    list_display = ('id', 'get_coliver_name', 'amount', 'status', 'due_date', 'is_automatic', 'created_at', 'view_proof')
    list_filter = (
        ColiverFilter,
        'status',
        PriceRangeFilter,
        DueDateStatusFilter,
        ('created_at', admin.DateFieldListFilter),
        ('due_date', admin.DateFieldListFilter),
    )
    search_fields = ('user__username', 'transaction_id', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    list_per_page = 50
    date_hierarchy = 'due_date'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'amount', 'description', 'due_date', 'status')
        }),
        ('Payment Details', {
            'fields': ('transaction_id', 'payment_proof', 'payment_method')
        }),
        ('Notes', {
            'fields': ('admin_notes', 'rejection_note', 'user_notes')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def get_coliver_name(self, obj):
        try:
            coliver = Coliver.objects.filter(user=obj.user).order_by('-created_at').first()
            if coliver:
                return f"{coliver.first_name} {coliver.last_name}"
        except Coliver.DoesNotExist:
            pass
        return obj.user.username
    get_coliver_name.short_description = 'Coliver'
    get_coliver_name.admin_order_field = 'user__username'

    def is_automatic(self, obj):
        """Show if this payment was created automatically"""
        try:
            # Check if there's an associated AutomaticPayment
            return hasattr(obj, 'automatic_payment') and obj.automatic_payment is not None
        except:
            return False
    is_automatic.boolean = True
    is_automatic.short_description = 'Auto'

    def view_proof(self, obj):
        if obj.payment_proof:
            return format_html('<a href="{}" target="_blank">View Proof</a>', obj.payment_proof.url)
        return "No proof uploaded"
    view_proof.short_description = 'Payment Proof'

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Payment)
class PaymentAdmin(BasePaymentAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).exclude(status='cancelled')

@admin.register(ArchivedPayment)
class ArchivedPaymentAdmin(BasePaymentAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='cancelled')

    class Media:
        css = {
            'all': ('admin/css/archived.css',)
        }


class AutomaticPaymentTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = AutomaticPaymentTemplate
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        amount_type = cleaned_data.get('amount_type')
        fixed_amount = cleaned_data.get('fixed_amount')
        percentage = cleaned_data.get('percentage')

        if amount_type == 'fixed' and not fixed_amount:
            raise forms.ValidationError('Fixed amount is required when amount type is "Fixed Amount".')
        
        if amount_type == 'percentage_cost' and not percentage:
            raise forms.ValidationError('Percentage is required when amount type is "Percentage of Total Cost".')
        
        return cleaned_data


@admin.register(AutomaticPaymentTemplate)
class AutomaticPaymentTemplateAdmin(admin.ModelAdmin):
    form = AutomaticPaymentTemplateAdminForm
    list_display = ('title', 'amount_type', 'date_type', 'days_offset', 'is_active', 'applies_to_all_colivers', 'created_at', 'generate_payments_action')
    list_filter = ('is_active', 'amount_type', 'date_type', 'applies_to_all_colivers', 'created_at')
    search_fields = ('title', 'description_template')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description_template')
        }),
        ('Date Configuration', {
            'fields': ('date_type', 'days_offset'),
            'description': 'Configure when this payment should be due relative to the coliver\'s stay dates.'
        }),
        ('Amount Configuration', {
            'fields': ('amount_type', 'fixed_amount', 'percentage'),
            'description': 'Configure how the payment amount should be calculated.'
        }),
        ('Settings', {
            'fields': ('is_active', 'applies_to_all_colivers')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def generate_payments_action(self, obj):
        """Custom action button to generate payments for all existing colivers"""
        from django.urls import reverse
        url = reverse('admin:generate_automatic_payments', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" onclick="return confirm(\'Generate payments for all colivers using this template?\')">Generate Payments</a>',
            url
        )
    generate_payments_action.short_description = 'Generate Payments'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                'generate-payments/<int:template_id>/',
                self.admin_site.admin_view(self.generate_payments_view),
                name='generate_automatic_payments',
            ),
        ]
        return custom_urls + urls

    def generate_payments_view(self, request, template_id):
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        
        template = get_object_or_404(AutomaticPaymentTemplate, pk=template_id)
        
        if template.applies_to_all_colivers:
            # Get all active colivers
            colivers = Coliver.objects.filter(is_active=True)
            created_count = 0
            
            for coliver in colivers:
                payment = template.create_payment_for_coliver(coliver, created_by=request.user)
                if payment:
                    created_count += 1
            
            if created_count > 0:
                messages.success(request, f'Successfully created {created_count} automatic payments using template "{template.title}".')
            else:
                messages.info(request, 'No new payments were created. All eligible colivers may already have payments for this template.')
        else:
            messages.warning(request, 'This template is not configured to apply to all colivers.')
        
        return redirect('admin:payments_automaticpaymenttemplate_changelist')


class AutomaticPaymentAdmin(admin.ModelAdmin):
    list_display = ('template', 'get_coliver_name', 'get_payment_amount', 'get_payment_status', 'get_payment_due_date', 'created_at')
    list_filter = ('template', 'payment__status', 'created_at')
    search_fields = ('coliver__first_name', 'coliver__last_name', 'template__title')
    readonly_fields = ('template', 'coliver', 'payment', 'created_at', 'created_by')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of automatic payments
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing of automatic payments
    
    def get_coliver_name(self, obj):
        return f"{obj.coliver.first_name} {obj.coliver.last_name}"
    get_coliver_name.short_description = 'Coliver'
    get_coliver_name.admin_order_field = 'coliver__first_name'
    
    def get_payment_amount(self, obj):
        return f"₩{obj.payment.amount:,.2f}"
    get_payment_amount.short_description = 'Amount'
    get_payment_amount.admin_order_field = 'payment__amount'
    
    def get_payment_status(self, obj):
        return obj.payment.get_status_display()
    get_payment_status.short_description = 'Status'
    get_payment_status.admin_order_field = 'payment__status'
    
    def get_payment_due_date(self, obj):
        return obj.payment.due_date
    get_payment_due_date.short_description = 'Due Date'
    get_payment_due_date.admin_order_field = 'payment__due_date'

admin.site.register(AutomaticPayment, AutomaticPaymentAdmin)
