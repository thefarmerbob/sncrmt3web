#!/usr/bin/env python3
"""
Test changing status of an EXISTING application to Onboarding
This simulates the real scenario: admin selects an existing application and changes status to "Onboarding"
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/maradumitru/sncrmt3/sncrmt3web')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sncrmt3web.settings')
django.setup()

from django.contrib.auth.models import User
from applications.models import Application
from colivers.models import Coliver
from payments.models import Payment, AutomaticPaymentTemplate, AutomaticPayment
from chapters.models import Chapter
from datetime import date, timedelta

def test_existing_application():
    print("🔧 Testing EXISTING Application Status Change: Existing App -> Onboarding -> Automatic Payments")
    print("=" * 90)
    
    # Step 1: Find or create an existing application with non-Onboarding status
    print("1️⃣ FINDING/CREATING EXISTING APPLICATION")
    print("-" * 50)
    
    # Look for existing applications with non-Onboarding status
    existing_apps = Application.objects.filter(
        application_status__in=['Submitted', 'Accepted', 'Interview passed']
    ).exclude(application_status='Onboarding')
    
    if existing_apps.exists():
        application = existing_apps.first()
        print(f"📋 Found existing application:")
        print(f"   Name: {application.first_name} {application.last_name}")
        print(f"   Status: {application.application_status}")
        print(f"   Created: {application.created_at}")
        print(f"   ID: {application.id}")
        
        # Use this application's user
        test_user = application.created_by
    else:
        print("📋 No existing applications found. Creating one and waiting...")
        
        # Create a user and application, then wait to simulate "existing"
        test_user, created = User.objects.get_or_create(
            username='existing_app_user',
            defaults={
                'email': 'existingapp@example.com',
                'first_name': 'Existing',
                'last_name': 'User',
                'is_active': True
            }
        )
        
        chapter = Chapter.objects.first()
        arrival_date = date.today() + timedelta(days=30)
        departure_date = arrival_date + timedelta(days=14)
        
        application = Application.objects.create(
            created_by=test_user,
            first_name='ExistingApp',
            last_name='Test',
            email='existingapp@example.com',
            date_join=arrival_date,
            date_leave=departure_date,
            chapter=chapter,
            application_status='Accepted',  # Start with non-onboarding status
            status='Submitted',
            member_type='new member',
            guests='1'
        )
        
        print(f"📝 Created application (simulating existing):")
        print(f"   Name: {application.first_name} {application.last_name}")
        print(f"   Status: {application.application_status}")
        print(f"   ID: {application.id}")
        
        # Wait a moment to simulate this being an "existing" application
        import time
        time.sleep(1)
    
    print()
    
    # Step 2: Check what currently exists for this user
    print("2️⃣ CHECKING CURRENT STATE")
    print("-" * 50)
    
    existing_colivers = Coliver.objects.filter(user=test_user)
    existing_payments = Payment.objects.filter(user=test_user)
    
    print(f"👤 User: {test_user.username}")
    print(f"📊 Current state:")
    print(f"   Application Status: {application.application_status}")
    print(f"   Existing Colivers: {existing_colivers.count()}")
    print(f"   Existing Payments: {existing_payments.count()}")
    
    if existing_colivers.exists():
        print(f"   Existing Coliver Details:")
        for coliver in existing_colivers:
            print(f"     - {coliver.first_name} {coliver.last_name} (ID: {coliver.id})")
    
    if existing_payments.exists():
        print(f"   Existing Payment Details:")
        for payment in existing_payments:
            print(f"     - {payment.description[:50]}... (₩{payment.amount:,.0f})")
    
    print()
    
    # Step 3: Check payment templates
    print("3️⃣ CHECKING PAYMENT TEMPLATES")
    print("-" * 50)
    
    templates = AutomaticPaymentTemplate.objects.filter(is_active=True, applies_to_all_colivers=True)
    print(f"📋 Active payment templates: {templates.count()}")
    for template in templates:
        print(f"   - {template.title}: {template.get_amount_type_display()}")
    
    print()
    
    # Step 4: Change application status to Onboarding
    print("4️⃣ CHANGING EXISTING APPLICATION TO ONBOARDING")
    print("-" * 50)
    
    print(f"🎯 Changing application {application.id} status from '{application.application_status}' to 'Onboarding'...")
    print(f"   This simulates admin selecting existing application and changing status...")
    
    # Store counts before change
    colivers_before = Coliver.objects.filter(user=test_user).count()
    payments_before = Payment.objects.filter(user=test_user).count()
    
    # Change the status (this is what admin does in the interface)
    old_status = application.application_status
    application.application_status = 'Onboarding'
    application.save()
    
    print(f"✅ Status changed from '{old_status}' to '{application.application_status}'")
    
    # Give time for signals and triggers
    import time
    time.sleep(3)
    
    print()
    
    # Step 5: Check what happened after status change
    print("5️⃣ CHECKING RESULTS AFTER STATUS CHANGE")
    print("-" * 50)
    
    colivers_after = Coliver.objects.filter(user=test_user).count()
    payments_after = Payment.objects.filter(user=test_user).count()
    
    print(f"📊 Results:")
    print(f"   Colivers: {colivers_after} (was {colivers_before})")
    print(f"   Payments: {payments_after} (was {payments_before})")
    
    # Check if new coliver was created
    new_colivers = Coliver.objects.filter(user=test_user).order_by('-created_at')
    if new_colivers.exists():
        print(f"\n👥 Coliver Records:")
        for i, coliver in enumerate(new_colivers):
            status_text = "🆕 NEW" if i == 0 and colivers_after > colivers_before else "📋 EXISTING"
            print(f"   {status_text} - {coliver.first_name} {coliver.last_name}")
            print(f"     Status: {coliver.status}")
            print(f"     Chapter: {coliver.chapter_name}")
            print(f"     Dates: {coliver.arrival_date} to {coliver.departure_date}")
            print(f"     Created: {coliver.created_at}")
            print(f"     ID: {coliver.id}")
    
    # Check payments
    all_payments = Payment.objects.filter(user=test_user).order_by('-created_at')
    if all_payments.exists():
        print(f"\n💰 Payment Records:")
        for i, payment in enumerate(all_payments):
            status_text = "🆕 NEW" if i < (payments_after - payments_before) else "📋 EXISTING"
            print(f"   {status_text} - {payment.description}")
            print(f"     Amount: ₩{payment.amount:,.2f}")
            print(f"     Due: {payment.due_date}")
            print(f"     Status: {payment.status}")
            print(f"     Created: {payment.created_at}")
            
            # Check if automatic
            try:
                auto_payment = AutomaticPayment.objects.get(payment=payment)
                print(f"     Template: {auto_payment.template.title} (AUTOMATIC)")
            except AutomaticPayment.DoesNotExist:
                print(f"     Template: Manual payment")
            print()
    
    print()
    
    # Step 6: Assessment
    print("6️⃣ ASSESSMENT")
    print("-" * 50)
    
    new_colivers_created = colivers_after > colivers_before
    new_payments_created = payments_after > payments_before
    expected_payments = templates.count()
    all_templates_applied = (payments_after - payments_before) == expected_payments
    
    results = [
        (new_colivers_created, "✅ Coliver created from existing application" if new_colivers_created else "❌ No new coliver created"),
        (new_payments_created, f"✅ Automatic payments created ({payments_after - payments_before} new)" if new_payments_created else "❌ No new payments created"),
        (all_templates_applied if new_payments_created else False, f"✅ All {expected_payments} templates applied" if all_templates_applied else f"⚠️ Only {payments_after - payments_before} of {expected_payments} templates applied" if new_payments_created else "❌ No templates applied")
    ]
    
    print("📊 Results Summary:")
    for success, message in results:
        print(f"   {message}")
    
    all_working = all(result[0] for result in results)
    
    print()
    if all_working:
        print("🎉 SUCCESS! Existing application workflow works correctly!")
        print("   ✅ Changing existing application to 'Onboarding' triggers automatic payments")
    else:
        print("❌ ISSUE DETECTED! The workflow for existing applications is not working correctly.")
        
        # Debug info
        print("\n🔍 DEBUG INFORMATION:")
        
        # Check signals
        from django.db.models import signals
        app_receivers = signals.post_save._live_receivers(sender=Application)
        print(f"📡 Application signals connected: {len(app_receivers)}")
        
        # Check if this specific application has any special characteristics
        print(f"🔍 Application details:")
        print(f"   PK: {application.pk}")
        print(f"   Created: {application.created_at}")
        print(f"   Modified: {application.modified_at}")
        print(f"   Current status: {application.application_status}")
    
    print("\n" + "=" * 90)
    print("🏁 Existing application test completed!")

if __name__ == "__main__":
    test_existing_application() 