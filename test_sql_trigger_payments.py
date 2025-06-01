#!/usr/bin/env python3
"""
Test the new comprehensive SQL trigger that creates both colivers AND payments
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

def test_sql_trigger_with_payments():
    print("🧪 Testing Comprehensive SQL Trigger: Application -> Onboarding -> Coliver + Payments")
    print("=" * 80)
    
    # Clean up test data
    test_user = User.objects.filter(username='sql_trigger_test').first()
    if test_user:
        Application.objects.filter(created_by=test_user).delete()
        Coliver.objects.filter(user=test_user).delete()
        Payment.objects.filter(user=test_user).delete()
        test_user.delete()
    
    # Create test user
    test_user = User.objects.create_user(
        username='sql_trigger_test',
        email='sqltriggertest@example.com',
        first_name='SQLTrigger',
        last_name='Test'
    )
    print(f"👤 Created test user: {test_user.username}")
    
    # Create application
    chapter = Chapter.objects.first()
    arrival_date = date.today() + timedelta(days=30)
    departure_date = arrival_date + timedelta(days=14)
    
    application = Application.objects.create(
        created_by=test_user,
        first_name='SQLTrigger',
        last_name='TestUser',
        email='sqltriggertest@example.com',
        date_join=arrival_date,
        date_leave=departure_date,
        chapter=chapter,
        application_status='Submitted',
        status='Submitted',
        member_type='new member',
        guests='1'
    )
    
    print(f"📝 Created application ID {application.id}")
    
    # Check before counts
    colivers_before = Coliver.objects.filter(user=test_user).count()
    payments_before = Payment.objects.filter(user=test_user).count()
    
    print(f"📊 Before status change:")
    print(f"   Colivers: {colivers_before}")
    print(f"   Payments: {payments_before}")
    
    # Change status to trigger SQL trigger
    print(f"\n🎯 Changing application status to 'Onboarding'...")
    application.application_status = 'Onboarding'
    application.save()
    
    # Give database time to process trigger
    import time
    time.sleep(2)
    
    # Check after counts
    colivers_after = Coliver.objects.filter(user=test_user).count()
    payments_after = Payment.objects.filter(user=test_user).count()
    
    print(f"📊 After status change:")
    print(f"   Colivers: {colivers_after} (was {colivers_before})")
    print(f"   Payments: {payments_after} (was {payments_before})")
    
    # Show detailed results
    if colivers_after > colivers_before:
        print(f"\n✅ COLIVER CREATED:")
        coliver = Coliver.objects.filter(user=test_user).first()
        print(f"   Name: {coliver.first_name} {coliver.last_name}")
        print(f"   Status: {coliver.status}")
        print(f"   Dates: {coliver.arrival_date} to {coliver.departure_date}")
        # Handle manual_cost safely
        try:
            manual_cost = float(coliver.manual_cost) if coliver.manual_cost else 0
            print(f"   Manual Cost: ₩{manual_cost:,.2f}")
        except (ValueError, TypeError):
            print(f"   Manual Cost: {coliver.manual_cost}")
    
    if payments_after > payments_before:
        print(f"\n✅ PAYMENTS CREATED ({payments_after - payments_before}):")
        payments = Payment.objects.filter(user=test_user).order_by('created_at')
        for i, payment in enumerate(payments, 1):
            print(f"   {i}. {payment.description}")
            print(f"      Amount: ₩{payment.amount:,.2f}")
            print(f"      Due: {payment.due_date}")
            print(f"      Status: {payment.status}")
            
            # Check AutomaticPayment link
            try:
                auto_payment = AutomaticPayment.objects.get(payment=payment)
                print(f"      Template: {auto_payment.template.title}")
            except AutomaticPayment.DoesNotExist:
                print(f"      Template: Not linked")
            print()
    
    # Assessment
    print("🔍 ASSESSMENT:")
    success_criteria = [
        (colivers_after > colivers_before, "Coliver created by SQL trigger"),
        (payments_after > payments_before, "Payments created by SQL trigger"),
        (payments_after == 2, "Both Security Deposit and Booking Payment created")
    ]
    
    all_passed = True
    for passed, description in success_criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {description}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 SUCCESS! SQL trigger is creating both colivers AND payments!")
        print("   This should now work reliably in the Django admin interface.")
    else:
        print("\n❌ ISSUE! SQL trigger is not working as expected.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_sql_trigger_with_payments() 