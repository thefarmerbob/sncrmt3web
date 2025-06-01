from .models import Coliver

def coliver_status(request):
    """Add is_coliver status to the template context for all views."""
    if request.user.is_authenticated:
        try:
            coliver = Coliver.objects.filter(user=request.user).order_by('-created_at').first()
            is_coliver = coliver is not None and coliver.is_active
        except Coliver.DoesNotExist:
            is_coliver = False
    else:
        is_coliver = False
    
    return {'is_coliver': is_coliver}