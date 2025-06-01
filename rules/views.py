from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Rule
from chapters.models import Chapter

# Create your views here.

@login_required
def rules_list(request):
    # Get selected chapters from query parameters
    selected_chapter_ids = request.GET.getlist('chapters')
    
    # Get all active chapters for the filter
    chapters = Chapter.objects.all()
    
    # Base query for active rules
    rules_query = Rule.objects.filter(is_active=True)
    
    # If specific chapters are selected, filter rules for those chapters
    if selected_chapter_ids:
        rules_query = rules_query.filter(
            Q(chapters__id__in=selected_chapter_ids) | Q(chapters__isnull=True)
        ).distinct()
    
    active_rules = rules_query.order_by('order', '-created_at')
    
    return render(request, 'rules/rules_list.html', {
        'rules': active_rules,
        'chapters': chapters,
        'selected_chapter_ids': [int(id) for id in selected_chapter_ids] if selected_chapter_ids else []
    })
