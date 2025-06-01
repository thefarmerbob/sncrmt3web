#!/usr/bin/env python3
"""
Test Django signal handling for automatic payment creation.
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

def test_django_signals():
    print("🔧 Testing Django Signal Handling...")
    print("=" * 50)
    
    # Get or create a test user
    test_user, created = User.objects.get_or_create(
        username='signal_test_user',
        defaults={
            'email': 'signaltest@example.com',
            'first_name': 'Signal',
            'last_name': 'Test'
        }
    )
    print(f"👤 {'Created' if created else 'Found'} test user: {test_user.username}")
    
    # Get a chapter
    chapter = Chapter.objects.first()
    if not chapter:
        print("❌ No chapters found!")
        return
    
    # Clean up existing test data
    Application.objects.filter(
        created_by=test_user,
        first_name='SignalTest',
        last_name='User'
    ).delete()
    
    Coliver.objects.filter(
        user=test_user,
        first_name='SignalTest',
        last_name='User'
    ).delete()
    
    Payment.objects.filter(user=test_user).delete()
    
    print("🧹 Cleaned up existing test data")
    
    # Create application with accepted status
    arrival_date = date.today() + timedelta(days=30)
    departure_date = arrival_date + timedelta(days=14)
    
    application = Application.objects.create(
        created_by=test_user,
        first_name='SignalTest',
        last_name='User',
        email='signaltest@example.com',
        date_join=arrival_date,
        date_leave=departure_date,
        chapter=chapter,
        application_status='Accepted',
        status='Submitted'
    )
    
    print(f"📝 Created application: {application.first_name} {application.last_name}")
    print(f"   Status: {application.application_status}")
    
    # Check counts before
    colivers_before = Coliver.objects.filter(user=test_user).count()
    payments_before = Payment.objects.filter(user=test_user).count()
    
    print(f"🔍 Before status change:")
    print(f"   Colivers: {colivers_before}")
    print(f"   Payments: {payments_before}")
    
    # Change status to Onboarding using Django model save
    print("\n🚀 Changing application status to 'Onboarding' using Django save...")
    application.application_status = 'Onboarding'
    application.save()
    
    print("✅ Application status changed!")
    
    # Give signals time to process
    import time
    time.sleep(1)
    
    # Check results
    colivers_after = Coliver.objects.filter(user=test_user).count()
    payments_after = Payment.objects.filter(user=test_user).count()
    
    print(f"\n📊 After status change:")
    print(f"   Colivers: {colivers_after}")
    print(f"   Payments: {payments_after}")
    
    # Show detailed results
    if colivers_after > colivers_before:
        print(f"✅ Created {colivers_after - colivers_before} coliver(s)")
        
        coliver = Coliver.objects.filter(user=test_user).first()
        print(f"👥 Coliver: {coliver.first_name} {coliver.last_name}")
        print(f"   Chapter: {coliver.chapter_name}")
        print(f"   Dates: {coliver.arrival_date} to {coliver.departure_date}")
        print(f"   Total cost: {coliver.total_cost}")
    
    if payments_after > payments_before:
        print(f"✅ Created {payments_after - payments_before} payment(s)")
        
        payments = Payment.objects.filter(user=test_user)
        for payment in payments:
            print(f"💰 Payment: {payment.description}")
            print(f"   Amount: ₩{payment.amount:,.2f}")
            print(f"   Due: {payment.due_date}")
            
            # Check if automatic
            try:
                auto_payment = AutomaticPayment.objects.get(payment=payment)
                print(f"   Template: {auto_payment.template.title} (AUTOMATIC)")
            except AutomaticPayment.DoesNotExist:
                print(f"   Template: Manual payment")
            print()
    else:
        print("❌ No automatic payments were created")
    
    print("=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_django_signals() 