from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.utils import timezone
from datetime import datetime
from .models import ChapterTransferRequest, TransferAcknowledgmentText
from chapters.models import Chapter
from colivers.models import Coliver

# Create your views here.

@login_required
def transfer_request_list(request):
    requests = ChapterTransferRequest.objects.filter(coliver=request.user)
    return render(request, 'chapter_transfers/transfer_request_list.html', {
        'requests': requests
    })

@login_required
def create_transfer_request(request):
    # Get the active coliver's current chapter
    try:
        coliver = Coliver.objects.get(user=request.user, is_active=True)
        current_chapter = coliver.chapter_name
        if not current_chapter:
            messages.error(request, 'You must be assigned to a chapter to request a transfer.')
            return redirect('dashboard:dashboard')
    except Coliver.DoesNotExist:
        messages.error(request, 'You must be an active coliver to request a chapter transfer.')
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        requested_chapter = get_object_or_404(Chapter, id=request.POST.get('requested_chapter'))
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        acknowledgment = request.POST.get('acknowledgment') == 'on'
        
        if not acknowledgment:
            messages.error(request, 'You must acknowledge the transfer conditions.')
            return redirect('chapter_transfers:create')
        
        # Validate chapters
        if current_chapter == requested_chapter:
            messages.error(request, 'Current and requested chapters cannot be the same.')
            return redirect('chapter_transfers:create')
        
        # Validate dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        today = timezone.now().date()
            
        if end_date < today:
            messages.error(request, 'End date cannot be in the past.')
            return redirect('chapter_transfers:create')
            
        if start_date < today:
            messages.error(request, 'Start date cannot be in the past.')
            return redirect('chapter_transfers:create')
        
        ChapterTransferRequest.objects.create(
            coliver=request.user,
            current_chapter=current_chapter,
            requested_chapter=requested_chapter,
            start_date=start_date,
            end_date=end_date,
            reason=request.POST.get('reason'),
            status='pending',
            acknowledgment=acknowledgment
        )
        
        return redirect('dashboard:dashboard')
    
    # Get the active acknowledgment text or use the default from the model
    acknowledgment_text = TransferAcknowledgmentText.objects.filter(is_active=True).first()
    if not acknowledgment_text:
        acknowledgment_text = TransferAcknowledgmentText.objects.create(is_active=True)

    chapters = Chapter.objects.all().order_by('name')
    return render(request, 'chapter_transfers/create_transfer_request.html', {
        'chapters': chapters,
        'current_chapter': current_chapter,
        'acknowledgment_text': acknowledgment_text.text
    })

@login_required
def transfer_request_detail(request, pk):
    transfer_request = get_object_or_404(ChapterTransferRequest, pk=pk, coliver=request.user)
    return render(request, 'chapter_transfers/transfer_request_detail.html', {
        'transfer_request': transfer_request
    })
