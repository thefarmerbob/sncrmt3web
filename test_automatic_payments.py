#!/usr/bin/env python3
"""
Test script to verify automatic payment creation when application status changes to ONBOARDING.
Run this with: python test_automatic_payments.py
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

def test_automatic_payment_creation():
    print("🔧 Testing Automatic Payment Creation...")
    print("=" * 50)
    
    # Check if we have active templates
    active_templates = AutomaticPaymentTemplate.objects.filter(is_active=True)
    print(f"📋 Found {active_templates.count()} active payment templates:")
    for template in active_templates:
        print(f"  - {template.title} ({template.get_amount_type_display()})")
    
    if not active_templates.exists():
        print("❌ No active payment templates found! Run: python manage.py setup_default_payment_templates")
        return
    
    print()
    
    # Get or create a test user
    test_user, created = User.objects.get_or_create(
        username='test_payment_user',
        defaults={
            'email': 'test_payment@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    print(f"👤 {'Created' if created else 'Found'} test user: {test_user.username}")
    
    # Get a chapter
    chapter = Chapter.objects.first()
    if not chapter:
        print("❌ No chapters found! Please create a chapter first.")
        return
    
    print(f"🏠 Using chapter: {chapter.name}")
    
    # Create a test application
    arrival_date = date.today() + timedelta(days=30)
    departure_date = arrival_date + timedelta(days=14)
    
    # Delete any existing test applications/colivers
    Application.objects.filter(
        created_by=test_user,
        first_name='AutoTest',
        last_name='Payment'
    ).delete()
    
    Coliver.objects.filter(
        user=test_user,
        first_name='AutoTest',
        last_name='Payment'
    ).delete()
    
    application = Application.objects.create(
        created_by=test_user,
        first_name='AutoTest',
        last_name='Payment',
        email='autotest@example.com',
        date_join=arrival_date,
        date_leave=departure_date,
        chapter=chapter,
        application_status='Accepted',  # Start with non-onboarding status
        status='Submitted'
    )
    
    print(f"📝 Created test application: {application.first_name} {application.last_name}")
    print(f"   Status: {application.application_status}")
    print(f"   Dates: {application.date_join} to {application.date_leave}")
    
    # Check payments before status change
    payments_before = Payment.objects.filter(user=test_user).count()
    colivers_before = Coliver.objects.filter(user=test_user).count()
    
    print(f"🔍 Before status change:")
    print(f"   Payments: {payments_before}")
    print(f"   Colivers: {colivers_before}")
    
    print("\n🚀 Changing application status to ONBOARDING...")
    
    # Change status to ONBOARDING - this should trigger the automatic payment creation
    application.application_status = 'Onboarding'
    application.save()
    
    print("✅ Application status changed!")
    
    # Give some time for signals and triggers to process
    import time
    time.sleep(1)
    
    # Check results
    payments_after = Payment.objects.filter(user=test_user).count()
    colivers_after = Coliver.objects.filter(user=test_user).count()
    
    print(f"\n📊 After status change:")
    print(f"   Payments: {payments_after}")
    print(f"   Colivers: {colivers_after}")
    
    # Show detailed results
    colivers = Coliver.objects.filter(user=test_user)
    for coliver in colivers:
        print(f"\n👥 Found coliver: {coliver.first_name} {coliver.last_name}")
        print(f"   Chapter: {coliver.chapter_name}")
        print(f"   Dates: {coliver.arrival_date} to {coliver.departure_date}")
        print(f"   Total cost: {coliver.total_cost}")
        
        # Show payments for this coliver
        payments = Payment.objects.filter(user=test_user)
        print(f"\n💰 Payments created:")
        for payment in payments:
            print(f"   - {payment.description}")
            print(f"     Amount: ₩{payment.amount:,.2f}")
            print(f"     Due: {payment.due_date}")
            print(f"     Status: {payment.status}")
            
            # Check if it's automatic
            try:
                auto_payment = AutomaticPayment.objects.get(payment=payment)
                print(f"     Template: {auto_payment.template.title} (AUTOMATIC)")
            except AutomaticPayment.DoesNotExist:
                print(f"     Template: Manual payment")
            print()
    
    if payments_after > payments_before:
        print(f"✅ SUCCESS! Created {payments_after - payments_before} automatic payment(s)")
    else:
        print("❌ FAILED! No automatic payments were created")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_automatic_payment_creation() 