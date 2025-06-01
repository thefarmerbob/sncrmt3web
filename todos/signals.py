from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from applications.models import Application
from .models import Todo

@receiver(post_save, sender=Application)
def create_application_todo(sender, instance, created, **kwargs):
    applicant_name = f"{instance.first_name} {instance.last_name}"
    
    if created:
        # Create a todo for new applications
        Todo.objects.create(
            title=f'Review application for {applicant_name}',
            description=f'New application submitted by {applicant_name} needs review.',
            task_type='application_review',
            reference_id=str(instance.id),
            coliver_name=applicant_name
        )
    elif instance.status == 'proof_submitted' and instance.application_status != 'approved':
        # Create a todo when proof is submitted
        Todo.objects.create(
            title=f'Review proof for {applicant_name}',
            description=f'Application proof submitted by {applicant_name} needs review.',
            task_type='application_review',
            reference_id=str(instance.id),
            coliver_name=applicant_name
        ) 