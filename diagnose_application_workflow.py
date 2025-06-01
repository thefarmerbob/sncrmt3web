#!/usr/bin/env python3
"""
Diagnostic script to help identify why automatic payments might not be working
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

def diagnose_workflow():
    print("🔍 DIAGNOSTIC: Automatic Payment Workflow")
    print("=" * 60)
    
    # 1. Check system components
    print("1️⃣ SYSTEM COMPONENTS CHECK")
    print("-" * 30)
    
    # Check payment templates
    templates = AutomaticPaymentTemplate.objects.filter(is_active=True)
    print(f"📋 Payment Templates: {templates.count()} total, {templates.filter(applies_to_all_colivers=True).count()} apply to all colivers")
    
    if not templates.exists():
        print("❌ No payment templates found!")
        print("   Run: python manage.py setup_default_payment_templates")
        return
    
    for template in templates:
        print(f"   - {template.title}: {template.get_amount_type_display()} ({'Active' if template.is_active else 'Inactive'})")
    
    # Check signals
    from django.db.models import signals
    app_receivers = signals.post_save._live_receivers(sender=Application)
    print(f"📡 Application signals: {len(app_receivers)} connected")
    
    coliver_receivers = signals.post_save._live_receivers(sender=Coliver)
    print(f"📡 Coliver signals: {len(coliver_receivers)} connected")
    
    # Check SQL trigger
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SHOW TRIGGERS LIKE 'after_application_update'")
        trigger = cursor.fetchone()
        if trigger:
            print("✅ SQL trigger exists")
        else:
            print("❌ SQL trigger missing")
    
    print()
    
    # 2. Find applications that could be tested
    print("2️⃣ AVAILABLE TEST APPLICATIONS")
    print("-" * 30)
    
    # Find applications with non-onboarding status
    test_candidates = Application.objects.filter(
        application_status__in=['Submitted', 'Accepted', 'Interview passed', 'Application in progress']
    ).exclude(application_status='Onboarding')[:5]
    
    if not test_candidates.exists():
        print("❌ No suitable test applications found")
        print("   All applications are either already 'Onboarding' or have other statuses")
    else:
        print(f"📋 Found {test_candidates.count()} applications that could be tested:")
        for app in test_candidates:
            user_colivers = Coliver.objects.filter(user=app.created_by).count()
            user_payments = Payment.objects.filter(user=app.created_by).count()
            print(f"   ID {app.id}: {app.first_name} {app.last_name} (Status: {app.application_status})")
            print(f"     User: {app.created_by.username}, Existing Colivers: {user_colivers}, Payments: {user_payments}")
    
    print()
    
    # 3. Check for common issues
    print("3️⃣ COMMON ISSUES CHECK")
    print("-" * 30)
    
    issues_found = []
    
    # Check if templates apply to all colivers
    all_apply_templates = templates.filter(applies_to_all_colivers=True)
    if not all_apply_templates.exists():
        issues_found.append("❌ No templates set to 'applies_to_all_colivers=True'")
    else:
        print(f"✅ {all_apply_templates.count()} templates apply to all colivers")
    
    # Check if there are any chapters
    chapters = Chapter.objects.all()
    if not chapters.exists():
        issues_found.append("❌ No chapters exist")
    else:
        print(f"✅ {chapters.count()} chapters available")
    
    # Check if signals module is imported
    try:
        import payments.signals
        print("✅ Signals module imported successfully")
    except ImportError as e:
        issues_found.append(f"❌ Signals module import error: {e}")
    
    if issues_found:
        print("\n⚠️ ISSUES FOUND:")
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print("✅ No obvious issues detected")
    
    print()
    
    # 4. Provide manual test instructions
    print("4️⃣ MANUAL TEST INSTRUCTIONS")
    print("-" * 30)
    
    if test_candidates.exists():
        app = test_candidates.first()
        print(f"🎯 Try manually testing with Application ID {app.id}:")
        print(f"   Name: {app.first_name} {app.last_name}")
        print(f"   Current Status: {app.application_status}")
        print()
        print("📝 Steps to test manually:")
        print("   1. Go to Django Admin → Applications → Active Applications")
        print(f"   2. Find application ID {app.id} ({app.first_name} {app.last_name})")
        print("   3. Click to edit it")
        print("   4. Change 'Application status' from '{}' to 'Onboarding'".format(app.application_status))
        print("   5. Click 'Save'")
        print()
        print("🔍 Expected results:")
        print("   - A new coliver record should be created")
        print("   - 2 automatic payments should be created (Security Deposit + Booking Payment)")
        print()
        print(f"🔍 To verify results, check:")
        print(f"   - Colivers for user '{app.created_by.username}' before: {Coliver.objects.filter(user=app.created_by).count()}")
        print(f"   - Payments for user '{app.created_by.username}' before: {Payment.objects.filter(user=app.created_by).count()}")
    else:
        print("❌ No applications available for testing")
        print("   You may need to create a new application or change existing ones back to non-onboarding status")
    
    print()
    
    # 5. Quick fix suggestions
    print("5️⃣ QUICK FIXES TO TRY")
    print("-" * 30)
    
    print("🔧 If the system isn't working, try these in order:")
    print("   1. Restart Django server: python manage.py runserver")
    print("   2. Check templates: python manage.py shell -> AutomaticPaymentTemplate.objects.filter(is_active=True)")
    print("   3. Re-run setup: python manage.py setup_default_payment_templates")
    print("   4. Check signals are loaded: python manage.py shell -> import payments.signals")
    print("   5. Test with a new application rather than existing one")
    
    print("\n" + "=" * 60)
    print("🏁 Diagnostic completed!")

if __name__ == "__main__":
    diagnose_workflow() 