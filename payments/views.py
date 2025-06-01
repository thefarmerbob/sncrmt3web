from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator
from django.utils import timezone
from .models import Payment
from django.urls import reverse

# Create your views here.

@login_required
def payment_list(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    pending_payments = payments.filter(status__in=['requested', 'rejected'])
    completed_payments = payments.filter(status__in=['proof_submitted', 'approved'])
    
    return render(request, 'payments/payment_list.html', {
        'pending_payments': pending_payments,
        'completed_payments': completed_payments
    })

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if request.method == 'POST' and 'payment_proof' in request.FILES:
        payment.payment_proof = request.FILES['payment_proof']
        payment.payment_method = request.POST.get('payment_method')
        payment.user_notes = request.POST.get('user_notes', '')
        payment.status = 'proof_submitted'
        payment.save()
        return redirect('dashboard:dashboard')
    
    return render(request, 'payments/payment_detail.html', {
        'payment': payment
    })

@login_required
def dashboard_payments(request):
    pending_payments = Payment.objects.filter(
        user=request.user,
        status__in=['requested', 'rejected']
    ).order_by('due_date')
    
    overdue_payments = [p for p in pending_payments if p.is_overdue]
    upcoming_payments = [p for p in pending_payments if not p.is_overdue]
    
    return render(request, 'payments/dashboard_payments.html', {
        'overdue_payments': overdue_payments,
        'upcoming_payments': upcoming_payments
    })
