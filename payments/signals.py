from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment, AutomaticPaymentTemplate, AutomaticPayment
from todos.models import Todo
from colivers.models import Coliver

@receiver(post_save, sender=Payment)
def create_payment_todo(sender, instance, created, **kwargs):
    """Create a todo item when payment proof is submitted"""
    # Get the coliver's name
    try:
        coliver = Coliver.objects.filter(user=instance.user).order_by('-created_at').first()
        if coliver:
            coliver_name = f"{coliver.first_name} {coliver.last_name}"
        else:
            coliver_name = instance.user.get_full_name() or instance.user.username
    except:
        coliver_name = instance.user.get_full_name() or instance.user.username

    # Only create a todo when status changes to proof_submitted and there are no existing todos
    if (instance.status == 'proof_submitted' and 
        not Todo.objects.filter(
            task_type='payment_review',
            reference_id=str(instance.id)
        ).exists()):
        Todo.objects.create(
            title=f'Review payment: {instance.description}',
            description=f'Review payment proof for {instance.amount} KRW submitted by {coliver_name}',
            task_type='payment_review',
            reference_id=str(instance.id),
            due_date=timezone.now() + timezone.timedelta(days=2),
            created_by=instance.created_by,
            coliver_name=coliver_name
        )

@receiver(post_save, sender=Coliver)
def create_automatic_payments_for_coliver(sender, instance, created, **kwargs):
    """Create automatic payments when a new coliver is created or when an existing coliver is updated"""
    # Only process if this is a new coliver or if key fields have changed
    if created or (instance.pk and hasattr(instance, '_state') and instance._state.adding):
        # Get all active automatic payment templates
        templates = AutomaticPaymentTemplate.objects.filter(is_active=True, applies_to_all_colivers=True)
        
        for template in templates:
            try:
                # Create automatic payment for this coliver
                payment = template.create_payment_for_coliver(instance)
                if payment:
                    print(f"Created automatic payment '{template.title}' for {instance.first_name} {instance.last_name}")
            except Exception as e:
                print(f"Error creating automatic payment '{template.title}' for {instance.first_name} {instance.last_name}: {e}")
    
    # Also handle updates to existing colivers if dates or cost-related fields change
    elif not created and instance.pk:
        try:
            # Get the old instance to compare
            old_instance = Coliver.objects.get(pk=instance.pk)
            
            # Check if relevant fields have changed
            fields_changed = (
                old_instance.arrival_date != instance.arrival_date or
                old_instance.departure_date != instance.departure_date or
                old_instance.chapter_name != instance.chapter_name or
                old_instance.manual_cost != instance.manual_cost
            )
            
            if fields_changed:
                # Update existing automatic payments for this coliver
                automatic_payments = AutomaticPayment.objects.filter(coliver=instance)
                
                for auto_payment in automatic_payments:
                    template = auto_payment.template
                    payment = auto_payment.payment
                    
                    # Only update if payment hasn't been processed yet
                    if payment.status == 'requested':
                        # Recalculate amount and due date
                        new_amount = template.calculate_amount(instance)
                        new_due_date = template.calculate_due_date(instance)
                        
                        # Update the payment
                        payment.amount = new_amount
                        payment.due_date = new_due_date
                        
                        # Update description with new details
                        payment.description = template.description_template.format(
                            coliver_name=f"{instance.first_name} {instance.last_name}",
                            chapter_name=instance.chapter_name.name if instance.chapter_name else "No Chapter",
                            arrival_date=instance.arrival_date.strftime('%Y-%m-%d') if instance.arrival_date else "TBD",
                            departure_date=instance.departure_date.strftime('%Y-%m-%d') if instance.departure_date else "TBD"
                        )
                        
                        payment.save()
                        print(f"Updated automatic payment '{template.title}' for {instance.first_name} {instance.last_name}")
                        
        except Coliver.DoesNotExist:
            # This shouldn't happen, but just in case
            pass
        except Exception as e:
            print(f"Error updating automatic payments for {instance.first_name} {instance.last_name}: {e}")


# Import Application model here to avoid circular imports
from applications.models import Application

# Store the old application status before save
_application_old_status = {}

@receiver(pre_save, sender=Application)
def store_old_application_status(sender, instance, **kwargs):
    """Store the old application status before it's changed"""
    if instance.pk:
        try:
            old_instance = Application.objects.get(pk=instance.pk)
            _application_old_status[instance.pk] = old_instance.application_status
        except Application.DoesNotExist:
            _application_old_status[instance.pk] = None

@receiver(post_save, sender=Application)
def create_automatic_payments_for_onboarding_application(sender, instance, created, **kwargs):
    """Create automatic payments when an application status changes to ONBOARDING"""
    
    # DISABLED: This functionality is now handled directly in the Application model's save method
    # to ensure it always works regardless of signal issues
    return
    
    # Debug output
    print(f"🔔 Application signal fired for {instance.first_name} {instance.last_name}")
    print(f"   Created: {created}")
    print(f"   Status: {instance.application_status}")
    
    if not created and instance.pk:
        # Get the old status from our stored values
        old_status = _application_old_status.get(instance.pk)
        
        print(f"   Old status: {old_status}")
        print(f"   New status: {instance.application_status}")
        
        # Check if application_status changed to 'Onboarding' (case insensitive)
        if (old_status and old_status.lower() != 'onboarding' and 
            instance.application_status.lower() == 'onboarding'):
            
            print(f"🎯 Application status changed to ONBOARDING for {instance.first_name} {instance.last_name}")
            
            # Create or update coliver - use more specific lookup to avoid conflicts
            coliver, coliver_created = Coliver.objects.get_or_create(
                user=instance.created_by,
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=instance.email,
                arrival_date=instance.date_join,
                departure_date=instance.date_leave,
                defaults={
                    'chapter_name': instance.chapter,
                    'status': 'ONBOARDING',
                    'manual_cost': instance.manual_cost,
                    'is_active': True
                }
            )
            
            if coliver_created:
                print(f"✓ Created new coliver record for {coliver.first_name} {coliver.last_name}")
            else:
                print(f"⚠ Found existing coliver for {coliver.first_name} {coliver.last_name}")
                # Update existing coliver with new application data
                coliver.chapter_name = instance.chapter
                coliver.manual_cost = instance.manual_cost
                coliver.status = 'ONBOARDING'
                coliver.is_active = True
                coliver.save()
                print(f"✓ Updated existing coliver with new application data")
            
            # ALWAYS create automatic payments for this application->coliver transition
            # Even if coliver existed, we need payments for this specific application
            templates = AutomaticPaymentTemplate.objects.filter(
                is_active=True, 
                applies_to_all_colivers=True
            )
            
            payment_count = 0
            for template in templates:
                try:
                    # Check if payment already exists for this specific template and coliver
                    existing_auto_payment = AutomaticPayment.objects.filter(
                        template=template,
                        coliver=coliver
                    ).first()
                    
                    if existing_auto_payment:
                        print(f"⚠ Payment already exists for template '{template.title}' and coliver {coliver.first_name} {coliver.last_name}")
                        # Check if we need to update the existing payment with new application data
                        payment = existing_auto_payment.payment
                        if payment.status == 'requested':  # Only update if not yet processed
                            new_amount = template.calculate_amount(coliver)
                            new_due_date = template.calculate_due_date(coliver)
                            
                            # Update payment with recalculated values
                            payment.amount = new_amount
                            payment.due_date = new_due_date
                            
                            # Update description with new details
                            payment.description = template.description_template.format(
                                coliver_name=f"{coliver.first_name} {coliver.last_name}",
                                chapter_name=coliver.chapter_name.name if coliver.chapter_name else "No Chapter",
                                arrival_date=coliver.arrival_date.strftime('%Y-%m-%d') if coliver.arrival_date else "TBD",
                                departure_date=coliver.departure_date.strftime('%Y-%m-%d') if coliver.departure_date else "TBD"
                            )
                            
                            payment.save()
                            print(f"✓ Updated existing payment '{template.title}' for {coliver.first_name} {coliver.last_name}")
                            payment_count += 1
                    else:
                        # Create new automatic payment for this coliver
                        payment = template.create_payment_for_coliver(coliver)
                        if payment:
                            payment_count += 1
                            print(f"✓ Created new automatic payment '{template.title}' for {coliver.first_name} {coliver.last_name}")
                        
                except Exception as e:
                    print(f"✗ Error creating/updating automatic payment '{template.title}' for {coliver.first_name} {coliver.last_name}: {e}")
            
            if payment_count > 0:
                print(f"🎉 Successfully created/updated {payment_count} automatic payments for {coliver.first_name} {coliver.last_name}")
            else:
                print(f"⚠ No automatic payments were created/updated for {coliver.first_name} {coliver.last_name}")
        else:
            print(f"   ➡ Status change not relevant (old: {old_status}, new: {instance.application_status})")
        
        # Clean up the stored status
        if instance.pk in _application_old_status:
            del _application_old_status[instance.pk]
                
    else:
        print(f"   ➡ Not processing (created={created}, has_pk={instance.pk is not None})") 