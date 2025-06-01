from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from colivers.models import Coliver
from rules.models import Rule
from payments.models import Payment
from chapter_transfers.models import ChapterTransferRequest
from maintenance.models import MaintenanceRequest
from django.db import models
from django.contrib import messages

@login_required
def dashboard(request):
    # Check if the user is an active coliver
    try:
        # Get the most recent coliver record for this user
        coliver = Coliver.objects.filter(user=request.user).order_by('-created_at').first()
        is_coliver = coliver is not None and coliver.is_active
    except Coliver.DoesNotExist:
        coliver = None
        is_coliver = False
    
    # If not an active coliver, redirect to applications list with a message
    if not is_coliver:
        if coliver and not coliver.is_active:
            messages.warning(request, "Your coliver status is currently inactive. Please contact the administrators for more information.")
        else:
            messages.warning(request, "You need to be an active coliver to access the dashboard. Please complete your application first.")
        return redirect('applications_list')
    
    context = {
        'is_coliver': is_coliver,
    }
    
    # If user is an active coliver, get active rules for their chapter
    if is_coliver:
        # Get both chapter-specific rules and general rules (where chapters is empty)
        chapter_filter = models.Q(chapters__isnull=True) | models.Q(chapters__name=coliver.chapter_name)
        active_rules = Rule.objects.filter(chapter_filter, is_active=True).order_by('order', '-created_at')
        context['rules'] = active_rules

        # Get pending payments for the user
        pending_payments = Payment.objects.filter(
            user=request.user,
            status__in=['requested', 'rejected', 'proof_submitted']
        ).order_by('due_date')
        
        context['overdue_payments'] = [p for p in pending_payments if p.is_overdue]
        context['upcoming_payments'] = [p for p in pending_payments if not p.is_overdue]

        # Get past payments (only approved ones)
        context['past_payments'] = Payment.objects.filter(
            user=request.user,
            status='approved'
        ).order_by('-created_at')[:5]  # Show last 5 payments

        # Get chapter transfer requests
        context['transfer_requests'] = ChapterTransferRequest.objects.filter(
            coliver=request.user
        ).order_by('-created_at')[:5]  # Show last 5 requests

        # Get maintenance requests (only pending ones)
        context['maintenance_requests'] = MaintenanceRequest.objects.filter(
            created_by=request.user,
            status='pending'
        ).order_by('-created_at')[:5]  # Show last 5 pending requests
    
    return render(request, 'dashboard/dashboard.html', context)