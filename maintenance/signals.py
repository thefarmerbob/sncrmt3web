from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from todos.models import Todo
from .models import MaintenanceRequest
from django.db import models
from django.utils import timezone
from django.core.cache import cache

@receiver(post_save, sender=MaintenanceRequest)
def handle_maintenance_todo(sender, instance, created, **kwargs):
    # Get the user's full name and details
    user = instance.created_by
    user_name = f"{user.first_name} {user.last_name}" if (user.first_name and user.last_name) else user.username
    
    # If status is pending, ensure there's a todo
    if instance.status == 'pending':
        # Check if a todo already exists
        existing_todo = Todo.objects.filter(
            task_type='maintenance_review',
            reference_id=str(instance.id)
        ).first()
        
        if not existing_todo:
            # Create a new todo
            Todo.objects.create(
                title=f'Review maintenance request: {instance.title}',
                description=(
                    f'Maintenance request from {user_name}:\n\n'
                    f'Title: {instance.title}\n'
                    f'Description: {instance.description}\n\n'
                    f'Please review and update the status accordingly.'
                ),
                task_type='maintenance_review',
                reference_id=str(instance.id),
                coliver_name=user_name
            )
    
    # If status is completed, mark all related todos as completed
    elif instance.status == 'completed':
        # Mark any existing review todos as completed using mark_as_completed()
        todos = Todo.objects.filter(
            task_type='maintenance_review',
            reference_id=str(instance.id),
            status='pending'
        )
        for todo in todos:
            todo.mark_as_completed()
        
        # Also mark any existing verification todos as completed
        verification_todos = Todo.objects.filter(
            task_type='maintenance_verification',
            reference_id=str(instance.id),
            status='pending'
        )
        for todo in verification_todos:
            todo.mark_as_completed()
        
        # Clear any cached querysets
        cache.clear() 