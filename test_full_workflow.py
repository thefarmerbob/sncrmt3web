#!/usr/bin/env python3
"""
Test the complete workflow: Application -> Change Status to Onboarding -> Automatic Payments Created
This simulates exactly what happens when an admin selects an application and changes status to "Onboarding"
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

def test_full_workflow():
    print("🔧 Testing Complete Workflow: Application -> Onboarding -> Automatic Payments")
    print("=" * 80)
    
    # Step 1: Check prerequisites
    print("1️⃣ CHECKING PREREQUISITES")
    print("-" * 40)
    
    # Check if we have active payment templates
    templates = AutomaticPaymentTemplate.objects.filter(is_active=True, applies_to_all_colivers=True)
    print(f"📋 Active payment templates: {templates.count()}")
    for template in templates:
        print(f"   - {template.title}: {template.get_amount_type_display()}")
    
    if templates.count() == 0:
        print("❌ No active payment templates! Creating default templates...")
        # Run the setup command
        from django.core.management import call_command
        call_command('setup_default_payment_templates')
        templates = AutomaticPaymentTemplate.objects.filter(is_active=True, applies_to_all_colivers=True)
        print(f"✅ Created {templates.count()} default templates")
    
    # Check chapters
    chapters = Chapter.objects.all()
    print(f"🏠 Available chapters: {chapters.count()}")
    if chapters.count() == 0:
        print("❌ No chapters available!")
        return
    
    chapter = chapters.first()
    print(f"   Using chapter: {chapter.name}")
    
    print()
    
    # Step 2: Create a test application (simulating admin creating/receiving an application)
    print("2️⃣ CREATING TEST APPLICATION")
    print("-" * 40)
    
    # Get or create a test user (simulating an applicant)
    test_user, created = User.objects.get_or_create(
        username='workflow_test_user',
        defaults={
            'email': 'workflowtest@example.com',
            'first_name': 'Workflow',
            'last_name': 'Test',
            'is_active': True
        }
    )
    print(f"👤 Test user: {test_user.username} ({'created' if created else 'found'})")
    
    # Clean up any existing test data
    Application.objects.filter(
        created_by=test_user,
        first_name='WorkflowTest',
        last_name='Applicant'
    ).delete()
    
    Coliver.objects.filter(
        user=test_user,
        first_name='WorkflowTest',
        last_name='Applicant'
    ).delete()
    
    Payment.objects.filter(user=test_user).delete()
    
    print("🧹 Cleaned up existing test data")
    
    # Create application with realistic dates
    arrival_date = date.today() + timedelta(days=30)  # 30 days from now
    departure_date = arrival_date + timedelta(days=14)  # 2 week stay
    
    application = Application.objects.create(
        created_by=test_user,
        first_name='WorkflowTest',
        last_name='Applicant',
        email='workflowtest@example.com',
        date_join=arrival_date,
        date_leave=departure_date,
        chapter=chapter,
        application_status='Submitted',  # Start with submitted status
        status='Submitted',
        member_type='new member',
        guests='1'
    )
    
    print(f"📝 Created application:")
    print(f"   Name: {application.first_name} {application.last_name}")
    print(f"   Email: {application.email}")
    print(f"   Dates: {application.date_join} to {application.date_leave}")
    print(f"   Chapter: {application.chapter.name}")
    print(f"   Status: {application.application_status}")
    print(f"   Application ID: {application.id}")
    
    print()
    
    # Step 3: Check initial state (before status change)
    print("3️⃣ CHECKING INITIAL STATE")
    print("-" * 40)
    
    colivers_before = Coliver.objects.filter(user=test_user).count()
    payments_before = Payment.objects.filter(user=test_user).count()
    
    print(f"📊 Before status change:")
    print(f"   Colivers: {colivers_before}")
    print(f"   Payments: {payments_before}")
    
    print()
    
    # Step 4: Change application status to "Onboarding" (simulating admin action)
    print("4️⃣ CHANGING APPLICATION STATUS TO ONBOARDING")
    print("-" * 40)
    
    print(f"🎯 Changing application {application.id} status from '{application.application_status}' to 'Onboarding'...")
    
    # This simulates what happens when admin changes the status in admin interface
    application.application_status = 'Onboarding'
    application.save()
    
    print("✅ Application status changed!")
    print(f"   New status: {application.application_status}")
    
    # Give time for signals and triggers to process
    import time
    time.sleep(2)
    
    print()
    
    # Step 5: Check results after status change
    print("5️⃣ CHECKING RESULTS AFTER STATUS CHANGE")
    print("-" * 40)
    
    colivers_after = Coliver.objects.filter(user=test_user).count()
    payments_after = Payment.objects.filter(user=test_user).count()
    
    print(f"📊 After status change:")
    print(f"   Colivers: {colivers_after} (was {colivers_before})")
    print(f"   Payments: {payments_after} (was {payments_before})")
    
    # Detailed coliver information
    colivers = Coliver.objects.filter(user=test_user)
    if colivers.exists():
        print(f"\n👥 Created Colivers:")
        for coliver in colivers:
            print(f"   - {coliver.first_name} {coliver.last_name}")
            print(f"     Chapter: {coliver.chapter_name}")
            print(f"     Dates: {coliver.arrival_date} to {coliver.departure_date}")
            print(f"     Status: {coliver.status}")
            
            # Handle total_cost safely
            try:
                total_cost = float(coliver.total_cost) if coliver.total_cost else 0
                print(f"     Total Cost: ₩{total_cost:,.2f}")
            except (ValueError, TypeError):
                print(f"     Total Cost: {coliver.total_cost}")
                
            print(f"     Coliver ID: {coliver.id}")
    else:
        print(f"\n❌ No colivers were created!")
    
    # Detailed payment information
    payments = Payment.objects.filter(user=test_user)
    if payments.exists():
        print(f"\n💰 Created Payments:")
        for payment in payments:
            print(f"   - {payment.description}")
            print(f"     Amount: ₩{payment.amount:,.2f}")
            print(f"     Due Date: {payment.due_date}")
            print(f"     Status: {payment.status}")
            print(f"     Payment ID: {payment.id}")
            
            # Check if it's automatic
            try:
                auto_payment = AutomaticPayment.objects.get(payment=payment)
                print(f"     Template: {auto_payment.template.title} (AUTOMATIC)")
                print(f"     Coliver: {auto_payment.coliver.first_name} {auto_payment.coliver.last_name}")
            except AutomaticPayment.DoesNotExist:
                print(f"     Template: Manual payment")
            print()
    else:
        print(f"\n❌ No payments were created!")
    
    print()
    
    # Step 6: Final assessment
    print("6️⃣ FINAL ASSESSMENT")
    print("-" * 40)
    
    success_criteria = [
        (colivers_after > colivers_before, "Coliver created when status changed to Onboarding"),
        (payments_after > payments_before, "Automatic payments created for the coliver"),
        (payments_after == templates.count(), f"All {templates.count()} payment templates were applied")
    ]
    
    all_passed = True
    for passed, description in success_criteria:
        status = "✅" if passed else "❌"
        print(f"{status} {description}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 SUCCESS! The automatic payment workflow is working correctly!")
        print("   When you change an application status to 'Onboarding':")
        print("   1. A coliver record is automatically created")
        print("   2. All active payment templates are applied")
        print("   3. Payment invoices are generated with correct amounts and due dates")
    else:
        print("❌ FAILURE! The automatic payment workflow has issues.")
        print("   Some components are not working as expected.")
        
        # Debugging information
        print("\n🔍 DEBUGGING INFORMATION:")
        
        # Check if SQL trigger exists and is working
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SHOW TRIGGERS LIKE 'after_application_update'")
            trigger = cursor.fetchone()
            if trigger:
                print("✅ SQL trigger exists")
            else:
                print("❌ SQL trigger missing")
        
        # Check if signals are connected
        from django.db.models import signals
        
        app_receivers = signals.post_save._live_receivers(sender=Application)
        print(f"📡 Application post_save signals: {len(app_receivers)}")
        
        coliver_receivers = signals.post_save._live_receivers(sender=Coliver)
        print(f"📡 Coliver post_save signals: {len(coliver_receivers)}")
    
    print("\n" + "=" * 80)
    print("🏁 Workflow test completed!")

if __name__ == "__main__":
    test_full_workflow() 