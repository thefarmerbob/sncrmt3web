from .models import Application
from colivers.models import Coliver

def user_applications(request):
    """Add user application status to the template context for all views."""
    if request.user.is_authenticated:
        has_draft_applications = Application.objects.filter(
            created_by=request.user,
            status='Draft',
            is_active=True
        ).exists()
        
        has_any_applications = Application.objects.filter(
            created_by=request.user,
            is_active=True
        ).exists()
        
        # Check if user is an active coliver
        try:
            coliver = Coliver.objects.filter(user=request.user).order_by('-created_at').first()
            is_coliver = coliver is not None and coliver.is_active
        except Coliver.DoesNotExist:
            is_coliver = False
        
        # Allow colivers to create new applications (for future stays, transfers, etc.)
        show_application_button = not has_any_applications or has_draft_applications or is_coliver
    else:
        has_draft_applications = False
        has_any_applications = False
        show_application_button = False
    
    return {
        'has_draft_applications': has_draft_applications,
        'has_any_applications': has_any_applications,
        'show_application_button': show_application_button
    } 