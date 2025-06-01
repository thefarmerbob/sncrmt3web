#!/usr/bin/env python3
"""
Debug script to check SQL trigger and coliver creation process.
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
from django.db import connection

def debug_coliver_creation():
    print("🔍 Debugging Coliver Creation Process...")
    print("=" * 60)
    
    # Check if SQL trigger exists
    with connection.cursor() as cursor:
        cursor.execute("SHOW TRIGGERS LIKE 'after_application_update'")
        trigger_exists = cursor.fetchone()
        if trigger_exists:
            print("✅ SQL trigger 'after_application_update' exists")
        else:
            print("❌ SQL trigger 'after_application_update' does NOT exist!")
            print("   Run the trigger.sql script to create it")
    
    # Get or create a test user
    test_user, created = User.objects.get_or_create(
        username='debug_user',
        defaults={
            'email': 'debug@example.com',
            'first_name': 'Debug',
            'last_name': 'User'
        }
    )
    print(f"👤 {'Created' if created else 'Found'} test user: {test_user.username}")
    
    # Get a chapter
    chapter = Chapter.objects.first()
    if not chapter:
        print("❌ No chapters found!")
        return
    
    print(f"🏠 Using chapter: {chapter.name} (ID: {chapter.id})")
    
    # Clean up any existing test data
    Application.objects.filter(
        created_by=test_user,
        first_name='DebugTest',
        last_name='User'
    ).delete()
    
    Coliver.objects.filter(
        user=test_user,
        first_name='DebugTest',
        last_name='User'
    ).delete()
    
    Payment.objects.filter(user=test_user).delete()
    
    print("🧹 Cleaned up existing test data")
    
    # Create application
    arrival_date = date.today() + timedelta(days=30)
    departure_date = arrival_date + timedelta(days=14)
    
    application = Application.objects.create(
        created_by=test_user,
        first_name='DebugTest',
        last_name='User',
        email='debugtest@example.com',
        date_join=arrival_date,
        date_leave=departure_date,
        chapter=chapter,
        application_status='Accepted',
        status='Submitted'
    )
    
    print(f"📝 Created application: {application.first_name} {application.last_name}")
    print(f"   Application ID: {application.id}")
    print(f"   User ID: {test_user.id}")
    print(f"   Chapter ID: {chapter.id}")
    print(f"   Status: {application.application_status}")
    
    # Check database state before status change
    colivers_before = Coliver.objects.filter(user=test_user).count()
    print(f"🔍 Colivers before status change: {colivers_before}")
    
    # Change status to trigger the SQL trigger
    print("\n🚀 Changing application status to 'Onboarding'...")
    
    # Direct SQL update to see what happens
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE applications_application 
            SET application_status = 'Onboarding' 
            WHERE id = %s
        """, [application.id])
        print(f"✅ Executed SQL UPDATE for application {application.id}")
    
    # Check if coliver was created by the trigger
    import time
    time.sleep(0.5)
    
    colivers_after = Coliver.objects.filter(user=test_user).count()
    print(f"🔍 Colivers after direct SQL update: {colivers_after}")
    
    if colivers_after > colivers_before:
        print("✅ SQL trigger successfully created coliver!")
        coliver = Coliver.objects.filter(user=test_user).first()
        print(f"👥 Coliver: {coliver.first_name} {coliver.last_name}")
        print(f"   ID: {coliver.id}")
        print(f"   Chapter: {coliver.chapter_name}")
        print(f"   Dates: {coliver.arrival_date} to {coliver.departure_date}")
        
        # Now test automatic payment creation manually
        print("\n💰 Testing automatic payment creation...")
        templates = AutomaticPaymentTemplate.objects.filter(is_active=True, applies_to_all_colivers=True)
        
        for template in templates:
            print(f"📋 Processing template: {template.title}")
            payment = template.create_payment_for_coliver(coliver)
            if payment:
                print(f"✅ Created payment: ₩{payment.amount:,.2f} due {payment.due_date}")
            else:
                print("⚠ Payment already exists or failed to create")
        
        # Check final payment count
        payments = Payment.objects.filter(user=test_user)
        print(f"\n💰 Total payments for user: {payments.count()}")
        for payment in payments:
            print(f"   - {payment.description}: ₩{payment.amount:,.2f}")
            
    else:
        print("❌ SQL trigger did NOT create coliver!")
        
        # Let's try the Django way
        print("\n🔄 Trying Django model save method...")
        
        # Refresh the application from database
        application.refresh_from_db()
        application.application_status = 'Onboarding'
        application.save()
        
        time.sleep(0.5)
        
        colivers_django = Coliver.objects.filter(user=test_user).count()
        print(f"🔍 Colivers after Django save: {colivers_django}")
        
        if colivers_django > colivers_before:
            print("✅ Django save method created coliver!")
        else:
            print("❌ Neither SQL trigger nor Django save created coliver!")
    
    print("\n" + "=" * 60)
    print("🏁 Debug completed!")

if __name__ == "__main__":
    debug_coliver_creation() 