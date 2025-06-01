from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from applications.models import Application
from colivers.models import Coliver
from .models import EmailTemplate, EmailLog, RecurringEmail


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'created_by', 'created_at', 'is_active', 'send_email_action', 'setup_recurring_action')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('name', 'subject', 'body')
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'subject', 'is_active')
        }),
        ('Email Content', {
            'fields': ('body',),
            'description': 'You can use placeholders like {{first_name}}, {{last_name}}, {{email}} in your template.'
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def send_email_action(self, obj):
        """Custom action button to send emails"""
        url = reverse('admin:send_template_email', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Send Now</a>',
            url
        )
    send_email_action.short_description = 'Send Email'

    def setup_recurring_action(self, obj):
        """Custom action button to setup recurring emails"""
        url = reverse('admin:setup_recurring_email', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Setup Recurring</a>',
            url
        )
    setup_recurring_action.short_description = 'Recurring Setup'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-email/<int:template_id>/',
                self.admin_site.admin_view(self.send_email_view),
                name='send_template_email',
            ),
            path(
                'send-email-process/<int:template_id>/',
                self.admin_site.admin_view(self.process_send_email),
                name='process_send_email',
            ),
            path(
                'setup-recurring/<int:template_id>/',
                self.admin_site.admin_view(self.setup_recurring_view),
                name='setup_recurring_email',
            ),
            path(
                'process-recurring/<int:template_id>/',
                self.admin_site.admin_view(self.process_recurring_setup),
                name='process_recurring_setup',
            ),
        ]
        return custom_urls + urls

    def send_email_view(self, request, template_id):
        """Custom admin view for sending emails"""
        template = EmailTemplate.objects.get(pk=template_id)
        
        # Get all applicants and colivers
        applicants = Application.objects.all().order_by('first_name', 'last_name')
        colivers = Coliver.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        context = {
            'template': template,
            'applicants': applicants,
            'colivers': colivers,
            'title': f'Send Email: {template.name}',
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        
        return render(request, 'admin/emails/send_email.html', context)

    def setup_recurring_view(self, request, template_id):
        """Custom admin view for setting up recurring emails"""
        template = EmailTemplate.objects.get(pk=template_id)
        
        context = {
            'template': template,
            'title': f'Setup Recurring Email: {template.name}',
            'opts': self.model._meta,
            'has_view_permission': True,
            'recipient_choices': RecurringEmail.RECIPIENT_CHOICES,
            'frequency_choices': RecurringEmail.FREQUENCY_CHOICES,
        }
        
        return render(request, 'admin/emails/setup_recurring.html', context)

    def process_recurring_setup(self, request, template_id):
        """Process the recurring email setup"""
        if request.method != 'POST':
            return redirect('admin:setup_recurring_email', template_id=template_id)
        
        template = EmailTemplate.objects.get(pk=template_id)
        
        name = request.POST.get('name')
        recipients = request.POST.get('recipients')
        frequency = request.POST.get('frequency')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time', '09:00')
        
        # Combine date and time
        from datetime import datetime
        next_send_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        next_send_datetime = timezone.make_aware(next_send_datetime)
        
        # Create recurring email
        RecurringEmail.objects.create(
            name=name,
            template=template,
            recipients=recipients,
            frequency=frequency,
            next_send_date=next_send_datetime,
            created_by=request.user,
            is_active=True
        )
        
        messages.success(request, f'Recurring email "{name}" has been set up successfully!')
        return redirect('admin:emails_recurringemail_changelist')

    def process_send_email(self, request, template_id):
        """Process the email sending"""
        if request.method != 'POST':
            return redirect('admin:send_template_email', template_id=template_id)
        
        template = EmailTemplate.objects.get(pk=template_id)
        
        # Get selected recipients
        selected_applicants = request.POST.getlist('applicants')
        selected_colivers = request.POST.getlist('colivers')
        
        sent_count = 0
        failed_count = 0
        
        # Send to selected applicants
        for app_id in selected_applicants:
            try:
                app = Application.objects.get(id=app_id)
                sent, failed = self._send_email_to_recipient(
                    template, app.email, f"{app.first_name} {app.last_name}", 
                    'applicant', request.user, {
                        'first_name': app.first_name,
                        'last_name': app.last_name,
                        'email': app.email,
                    }
                )
                sent_count += sent
                failed_count += failed
            except Exception as e:
                failed_count += 1
        
        # Send to selected colivers
        for coliver_id in selected_colivers:
            try:
                coliver = Coliver.objects.get(id=coliver_id)
                sent, failed = self._send_email_to_recipient(
                    template, coliver.email, f"{coliver.first_name} {coliver.last_name}", 
                    'coliver', request.user, {
                        'first_name': coliver.first_name,
                        'last_name': coliver.last_name,
                        'email': coliver.email,
                    }
                )
                sent_count += sent
                failed_count += failed
            except Exception as e:
                failed_count += 1
        
        # Show results
        if sent_count > 0:
            messages.success(request, f'Successfully sent {sent_count} emails!')
        if failed_count > 0:
            messages.error(request, f'{failed_count} emails failed to send.')
        
        return redirect('admin:emails_emailtemplate_changelist')

    def _send_email_to_recipient(self, template, email, name, recipient_type, sent_by, context_data, recurring_email=None):
        """Helper method to send email to a single recipient"""
        try:
            # Render template with context
            subject_template = Template(template.subject)
            body_template = Template(template.body)
            context = Context(context_data)
            
            rendered_subject = subject_template.render(context)
            rendered_body = body_template.render(context)
            
            # Create email log entry
            email_log = EmailLog.objects.create(
                template=template,
                recurring_email=recurring_email,
                recipient_email=email,
                recipient_name=name,
                recipient_type=recipient_type,
                subject=rendered_subject,
                body=rendered_body,
                sent_by=sent_by,
                status='pending'
            )
            
            # Send email
            try:
                send_mail(
                    subject=rendered_subject,
                    message=rendered_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                email_log.status = 'sent'
                email_log.save()
                return 1, 0  # sent, failed
                
            except Exception as e:
                email_log.status = 'failed'
                email_log.error_message = str(e)
                email_log.save()
                return 0, 1  # sent, failed
                
        except Exception as e:
            return 0, 1  # sent, failed


@admin.register(RecurringEmail)
class RecurringEmailAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'recipients', 'frequency', 'next_send_date', 'is_active', 'last_sent', 'send_now_action')
    list_filter = ('is_active', 'frequency', 'recipients', 'created_at')
    search_fields = ('name', 'template__name')
    readonly_fields = ('created_by', 'created_at', 'last_sent')
    
    fieldsets = (
        ('Recurring Email Setup', {
            'fields': ('name', 'template', 'recipients', 'frequency', 'next_send_date', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'last_sent'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def send_now_action(self, obj):
        """Custom action button to send recurring email now"""
        url = reverse('admin:send_recurring_now', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Send Now</a>',
            url
        )
    send_now_action.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-now/<int:recurring_id>/',
                self.admin_site.admin_view(self.send_recurring_now),
                name='send_recurring_now',
            ),
        ]
        return custom_urls + urls

    def send_recurring_now(self, request, recurring_id):
        """Send a recurring email immediately"""
        recurring_email = RecurringEmail.objects.get(pk=recurring_id)
        
        sent_count = 0
        failed_count = 0
        
        # Get recipients based on configuration
        if recurring_email.recipients in ['applicants', 'both']:
            applicants = Application.objects.all()
            for app in applicants:
                template_admin = EmailTemplateAdmin(EmailTemplate, admin.site)
                sent, failed = template_admin._send_email_to_recipient(
                    recurring_email.template, app.email, f"{app.first_name} {app.last_name}", 
                    'applicant', request.user, {
                        'first_name': app.first_name,
                        'last_name': app.last_name,
                        'email': app.email,
                    }, recurring_email
                )
                sent_count += sent
                failed_count += failed
        
        if recurring_email.recipients in ['colivers', 'both']:
            colivers = Coliver.objects.filter(is_active=True)
            for coliver in colivers:
                template_admin = EmailTemplateAdmin(EmailTemplate, admin.site)
                sent, failed = template_admin._send_email_to_recipient(
                    recurring_email.template, coliver.email, f"{coliver.first_name} {coliver.last_name}", 
                    'coliver', request.user, {
                        'first_name': coliver.first_name,
                        'last_name': coliver.last_name,
                        'email': coliver.email,
                    }, recurring_email
                )
                sent_count += sent
                failed_count += failed
        
        # Update last sent time and next send date
        recurring_email.last_sent = timezone.now()
        
        # Calculate next send date based on frequency
        if recurring_email.frequency == 'daily':
            recurring_email.next_send_date = timezone.now() + timedelta(days=1)
        elif recurring_email.frequency == 'weekly':
            recurring_email.next_send_date = timezone.now() + timedelta(weeks=1)
        elif recurring_email.frequency == 'monthly':
            recurring_email.next_send_date = timezone.now() + timedelta(days=30)
        
        recurring_email.save()
        
        # Show results
        if sent_count > 0:
            messages.success(request, f'Successfully sent {sent_count} emails!')
        if failed_count > 0:
            messages.error(request, f'{failed_count} emails failed to send.')
        
        return redirect('admin:emails_recurringemail_changelist')


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'recipient_name', 'recipient_type', 'subject', 'status', 'sent_by', 'sent_at', 'recurring_email')
    list_filter = ('status', 'recipient_type', 'sent_at', 'sent_by', 'template', 'recurring_email')
    search_fields = ('recipient_email', 'recipient_name', 'subject', 'template__name')
    readonly_fields = ('template', 'recurring_email', 'recipient_email', 'recipient_name', 'recipient_type', 
                      'subject', 'body', 'status', 'sent_by', 'sent_at', 'error_message')
    
    fieldsets = (
        ('Recipient Information', {
            'fields': ('recipient_email', 'recipient_name', 'recipient_type')
        }),
        ('Email Content', {
            'fields': ('template', 'recurring_email', 'subject', 'body')
        }),
        ('Status Information', {
            'fields': ('status', 'error_message', 'sent_by', 'sent_at')
        }),
    )

    def has_add_permission(self, request):
        # Prevent manual creation of email logs through admin
        return False

    def has_change_permission(self, request, obj=None):
        # Make email logs read-only
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow deletion for cleanup purposes
        return True
