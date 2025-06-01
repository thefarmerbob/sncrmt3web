from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, time
from todos.models import Todo
from .models import ChapterTransferRequest
from django.db import models
from colivers.models import Coliver

@receiver(post_save, sender=ChapterTransferRequest)
def handle_transfer_todo(sender, instance, created, **kwargs):
    # Get the coliver's full name and details
    coliver = instance.coliver
    coliver_name = f"{coliver.first_name} {coliver.last_name}" if (coliver.first_name and coliver.last_name) else coliver.username
    
    # Get coliver's departure date
    try:
        coliver_profile = Coliver.objects.get(user=coliver, is_active=True)
        departure_date = coliver_profile.departure_date if coliver_profile.departure_date else "TBD"
    except Coliver.DoesNotExist:
        departure_date = "TBD"
    
    # If status is pending, ensure there's a todo
    if instance.status == 'pending':
        # Check if a todo already exists
        existing_todo = Todo.objects.filter(
            task_type='transfer_review',
            reference_id=str(instance.id)
        ).first()
        
        if not existing_todo:
            # Convert start_date to datetime for due_date (set to end of day)
            due_datetime = None
            if instance.start_date:
                due_datetime = timezone.make_aware(
                    datetime.combine(instance.start_date, time(23, 59, 59))
                )
            
            # Create a new todo
            Todo.objects.create(
                title=f'Review transfer request from {coliver_name}',
                description=(
                    f'Transfer request from {coliver_name}:\n'
                    f'From: {instance.current_chapter.name}\n'
                    f'To: {instance.requested_chapter.name}\n'
                    f'End Date at Current Chapter: {instance.end_date}\n'
                    f'Start Date at New Chapter: {instance.start_date}\n\n'
                    f'Reason: {instance.reason}'
                ),
                task_type='transfer_review',
                reference_id=str(instance.id),
                coliver_name=coliver_name,
                due_date=due_datetime
            )
    # If status is not pending, mark any existing todo as completed
    else:
        Todo.objects.filter(
            task_type='transfer_review',
            reference_id=str(instance.id),
            status='pending'
        ).update(
            status='completed',
            completed_at=models.functions.Now()
        )
        
        # If the transfer was approved, create a new todo for administrative tasks
        if instance.status == 'approved':
            # Convert start_date to datetime for due_date (set to end of day)
            due_datetime = None
            if instance.start_date:
                due_datetime = timezone.make_aware(
                    datetime.combine(instance.start_date, time(23, 59, 59))
                )
            
            Todo.objects.create(
                title=f'Process chapter transfer for {coliver_name}',
                description=(
                    f'Administrative tasks for {coliver_name}\'s approved transfer:\n\n'
                    f'1. Update chapter bookings for {instance.requested_chapter.name}:\n'
                    f'   - Create booking from {instance.start_date} to {instance.end_date}\n'
                    f'   (This will be their new home chapter)\n\n'
                    f'2. Update chapter bookings for {instance.current_chapter.name}:\n'
                    f'   - Update end date to {instance.start_date}\n'
                    f'   - Add new booking from {instance.end_date} to {departure_date}\n\n'
                    f'3. Update coliver\'s chapter (Do this on {instance.start_date}):\n'
                    f'   - Change chapter from {instance.current_chapter.name} to {instance.requested_chapter.name}\n\n'
                ),
                task_type='transfer_review',
                reference_id=f"{instance.id}_admin",
                coliver_name=coliver_name,
                due_date=due_datetime
            ) 