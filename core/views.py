from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from colivers.models import Coliver

# Create your views here.
def core_router(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if the user is an active coliver
    try:
        coliver = Coliver.objects.filter(user=request.user).order_by('-created_at').first()
        is_active_coliver = coliver is not None and coliver.is_active
    except Coliver.DoesNotExist:
        is_active_coliver = False
    
    if is_active_coliver:
        return redirect('dashboard:dashboard')
    
    return redirect('applications_list')

def join(request):
    return render(request, 'core/join.html')
