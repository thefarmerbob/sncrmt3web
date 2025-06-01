from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.utils import timezone
from .models import MaintenanceRequest, MaintenanceConfirmationText
from .forms import MaintenanceRequestForm, MaintenanceRequestManagerForm

# Create your views here.

@login_required
def maintenance_create(request):
    # Get the active confirmation text
    confirmation_text = MaintenanceConfirmationText.objects.filter(is_active=True).first()
    if not confirmation_text:
        # Create a default one if none exists
        confirmation_text = MaintenanceConfirmationText.objects.create(
            text="I confirm that this maintenance request is accurate and needs attention",
            is_active=True
        )

    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            maintenance_request = form.save(commit=False)
            maintenance_request.created_by = request.user
            maintenance_request.save()
            return redirect('/dashboard/')
    else:
        form = MaintenanceRequestForm()
    
    return render(request, 'maintenance/maintenance_form.html', {
        'form': form,
        'title': 'Create Maintenance Request',
        'confirmation_text': confirmation_text.text
    })

@login_required
def maintenance_detail(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    # Get the active confirmation text
    confirmation_text = MaintenanceConfirmationText.objects.filter(is_active=True).first()
    if not confirmation_text:
        confirmation_text = MaintenanceConfirmationText.objects.create(
            text="I confirm that this maintenance request is accurate and needs attention",
            is_active=True
        )
    
    if request.user.is_staff:
        if request.method == 'POST':
            form = MaintenanceRequestManagerForm(request.POST, instance=maintenance_request)
            if form.is_valid():
                maintenance_request = form.save(commit=False)
                if maintenance_request.status == 'completed' and not maintenance_request.completed_at:
                    maintenance_request.completed_at = timezone.now()
                maintenance_request.save()
                return redirect('/dashboard/')
        else:
            form = MaintenanceRequestManagerForm(instance=maintenance_request)
    else:
        form = None
    
    return render(request, 'maintenance/maintenance_detail.html', {
        'maintenance_request': maintenance_request,
        'form': form,
        'confirmation_text': confirmation_text.text
    })
