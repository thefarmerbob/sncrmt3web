#!/usr/bin/env python3
"""
Create a fresh test application for manual testing
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

def create_test_application():
    print("🧪 Creating Fresh Test Application for Manual Testing")
    print("=" * 60)
    
    # Clean up any existing test data
    test_user = User.objects.filter(username='manual_test_user').first()
    if test_user:
        print("🧹 Cleaning up existing test data...")
        Application.objects.filter(created_by=test_user).delete()
        Coliver.objects.filter(user=test_user).delete()
        Payment.objects.filter(user=test_user).delete()
        test_user.delete()
    
    # Create test user
    test_user = User.objects.create_user(
        username='manual_test_user',
        email='manualtest@example.com',
        first_name='Manual',
        last_name='Test',
        password='testpass123'
    )
    print(f"👤 Created test user: {test_user.username}")
    
    # Get a chapter
    chapter = Chapter.objects.first()
    if not chapter:
        print("❌ No chapters available!")
        return
    
    # Create application
    arrival_date = date.today() + timedelta(days=21)  # 3 weeks from now
    departure_date = arrival_date + timedelta(days=28)  # 4 week stay
    
    application = Application.objects.create(
        created_by=test_user,
        first_name='Manual',
        last_name='TestUser',
        email='manualtest@example.com',
        date_join=arrival_date,
        date_leave=departure_date,
        chapter=chapter,
        application_status='Submitted',  # Start with submitted
        status='Submitted',
        member_type='new member',
        guests='1'
    )
    
    print(f"📝 Created test application:")
    print(f"   🆔 Application ID: {application.id}")
    print(f"   👤 Name: {application.first_name} {application.last_name}")
    print(f"   📧 Email: {application.email}")
    print(f"   📅 Dates: {application.date_join} to {application.date_leave}")
    print(f"   🏠 Chapter: {application.chapter.name}")
    print(f"   📊 Status: {application.application_status}")
    print(f"   👤 User: {application.created_by.username}")
    
    # Show current counts
    colivers = Coliver.objects.filter(user=test_user).count()
    payments = Payment.objects.filter(user=test_user).count()
    
    print(f"\n📊 Current counts for user '{test_user.username}':")
    print(f"   🏠 Colivers: {colivers}")
    print(f"   💰 Payments: {payments}")
    
    # Show templates that should be applied
    templates = AutomaticPaymentTemplate.objects.filter(is_active=True, applies_to_all_colivers=True)
    print(f"\n📋 Payment templates that should be applied ({templates.count()}):")
    for template in templates:
        print(f"   - {template.title}: {template.get_amount_type_display()}")
    
    print(f"\n🎯 MANUAL TEST INSTRUCTIONS:")
    print(f"═══════════════════════════════════════════════════════")
    print(f"1. Open Django Admin: http://127.0.0.1:8001/admin/")
    print(f"2. Login as admin")
    print(f"3. Go to Applications → Active Applications")
    print(f"4. Find Application ID {application.id} (Manual TestUser)")
    print(f"5. Click to edit it")
    print(f"6. Change 'Application status' from 'Submitted' to 'Onboarding'")
    print(f"7. Click 'Save'")
    print(f"")
    print(f"🔍 EXPECTED RESULTS:")
    print(f"   ✅ 1 new coliver should be created")
    print(f"   ✅ {templates.count()} automatic payments should be created")
    print(f"   ✅ You should see success messages in the admin")
    print(f"")
    print(f"🔍 TO VERIFY RESULTS:")
    print(f"   - Check Colivers → Coliver list (should show 1 for {test_user.username})")
    print(f"   - Check Payments → Payment list (should show {templates.count()} for {test_user.username})")
    print(f"")
    print(f"⚠️  If nothing happens, check the Django console for error messages!")
    
    print("\n" + "=" * 60)
    print("🏁 Test application created! Try the manual test above.")

if __name__ == "__main__":
    create_test_application() 