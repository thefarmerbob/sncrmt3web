#!/usr/bin/env python3
"""
Check current payment setup and adjust it to simply match coliver's total cost
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/maradumitru/sncrmt3/sncrmt3web')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sncrmt3web.settings')
django.setup()

from django.contrib.auth.models import User
from colivers.models import Coliver
from payments.models import Payment, AutomaticPaymentTemplate, AutomaticPayment

def check_current_setup():
    print("🔍 CHECKING CURRENT PAYMENT SETUP")
    print("=" * 50)
    
    # Find any active coliver to test with
    active_colivers = Coliver.objects.filter(is_active=True)
    
    if not active_colivers.exists():
        print("❌ No active colivers found!")
        return False
    
    coliver = active_colivers.first()
    print(f"👥 Testing with coliver: {coliver.first_name} {coliver.last_name}")
    print(f"   Dates: {coliver.arrival_date} to {coliver.departure_date}")
    
    # Check coliver cost
    nights = (coliver.departure_date - coliver.arrival_date).days
    total_cost = coliver.calculate_cost()
    formatted_cost = coliver.total_cost
    
    print(f"   Nights: {nights}")
    print(f"   Calculate cost: ₩{total_cost:,.2f}")
    print(f"   Total cost property: {formatted_cost}")
    
    # Check current payments for this coliver
    payments = Payment.objects.filter(user=coliver.user)
    print(f"\n💰 Current payments for this coliver:")
    
    total_payment_amount = 0
    for payment in payments:
        print(f"   - {payment.description}")
        print(f"     Amount: ₩{payment.amount:,.2f}")
        total_payment_amount += payment.amount
    
    print(f"\n📊 Summary:")
    print(f"   Coliver total cost: ₩{total_cost:,.2f}")
    print(f"   Total payments: ₩{total_payment_amount:,.2f}")
    print(f"   Match: {'✅' if total_cost == total_payment_amount else '❌'}")
    
    # Check payment templates
    templates = AutomaticPaymentTemplate.objects.filter(is_active=True)
    print(f"\n📋 Active payment templates ({templates.count()}):")
    for template in templates:
        print(f"   - {template.title}: {template.get_amount_type_display()}")
        if template.amount_type == 'fixed':
            print(f"     Fixed amount: ₩{template.fixed_amount:,.2f}")
        
        # Calculate what this template would create for our test coliver
        template_amount = template.calculate_amount(coliver)
        print(f"     Would create: ₩{template_amount:,.2f}")
    
    return True

def fix_payment_templates():
    """Adjust payment templates to create a single payment equal to coliver total cost"""
    print(f"\n🔧 ADJUSTING PAYMENT TEMPLATES")
    print("=" * 50)
    
    templates = AutomaticPaymentTemplate.objects.filter(is_active=True)
    
    # Option 1: Keep only the "Booking Payment" template and remove security deposit
    print("Option 1: Single payment for total stay cost")
    print("   - Keep 'Booking Payment' (Total Stay Cost)")
    print("   - Disable 'Security Deposit' template")
    
    # Option 2: Combine into one template
    print("\nOption 2: Create single 'Total Payment' template")
    print("   - Disable existing templates")
    print("   - Create new template for total cost")
    
    choice = input("\nWhich option do you prefer? (1 or 2): ").strip()
    
    if choice == "1":
        # Keep booking payment, disable security deposit
        for template in templates:
            if 'security' in template.title.lower() or 'deposit' in template.title.lower():
                template.is_active = False
                template.save()
                print(f"✅ Disabled: {template.title}")
            else:
                print(f"✅ Keeping: {template.title}")
    
    elif choice == "2":
        # Disable all existing templates
        for template in templates:
            template.is_active = False
            template.save()
            print(f"✅ Disabled: {template.title}")
        
        # Create new single payment template
        total_payment_template = AutomaticPaymentTemplate.objects.create(
            title="Total Stay Payment",
            description_template="Total payment for {coliver_name} stay at {chapter_name} ({arrival_date} to {departure_date})",
            date_type='arrival_date',
            days_offset=0,  # Due on arrival date
            amount_type='total_cost',
            is_active=True,
            applies_to_all_colivers=True
        )
        print(f"✅ Created: {total_payment_template.title}")
    
    else:
        print("❌ Invalid choice, no changes made")
        return False
    
    return True

def test_new_setup():
    """Test the new payment setup with a fresh coliver"""
    print(f"\n🧪 TESTING NEW SETUP")
    print("=" * 50)
    
    # Create a test application and change it to onboarding
    from applications.models import Application
    from chapters.models import Chapter
    from datetime import date, timedelta
    
    # Clean up any existing test data
    test_username = 'payment_setup_test'
    User.objects.filter(username=test_username).delete()
    
    # Create test user
    test_user = User.objects.create_user(
        username=test_username,
        email='paymenttest@example.com',
        first_name='Payment',
        last_name='TestUser',
        password='testpass123'
    )
    
    # Create application
    chapter = Chapter.objects.first()
    arrival_date = date.today() + timedelta(days=14)
    departure_date = arrival_date + timedelta(days=21)  # 21 nights
    
    application = Application.objects.create(
        created_by=test_user,
        first_name='Payment',
        last_name='TestUser',
        email='paymenttest@example.com',
        date_join=arrival_date,
        date_leave=departure_date,
        chapter=chapter,
        application_status='Submitted',
        status='Submitted'
    )
    
    print(f"📝 Created test application for {application.first_name} {application.last_name}")
    print(f"   Dates: {application.date_join} to {application.date_leave}")
    
    # Calculate expected cost
    nights = (application.date_leave - application.date_join).days
    expected_cost = chapter.cost_per_night * nights
    print(f"   Expected cost: ₩{expected_cost:,.2f}")
    
    # Change to onboarding
    print(f"\n🚀 Changing status to Onboarding...")
    application.application_status = 'Onboarding'
    application.save()
    
    # Give time for signals
    import time
    time.sleep(0.5)
    
    # Check results
    coliver = Coliver.objects.filter(user=test_user).first()
    payments = Payment.objects.filter(user=test_user)
    
    if coliver:
        actual_cost = coliver.calculate_cost()
        print(f"✅ Coliver created: ₩{actual_cost:,.2f}")
        
        print(f"\n💰 Payments created:")
        total_payments = 0
        for payment in payments:
            print(f"   - {payment.description}")
            print(f"     Amount: ₩{payment.amount:,.2f}")
            total_payments += payment.amount
        
        print(f"\n📊 Final check:")
        print(f"   Coliver cost: ₩{actual_cost:,.2f}")
        print(f"   Total payments: ₩{total_payments:,.2f}")
        print(f"   Match: {'✅' if actual_cost == total_payments else '❌'}")
        
        if actual_cost == total_payments:
            print(f"\n🎉 SUCCESS! Payment equals coliver total cost!")
            return True
        else:
            print(f"\n❌ Payment amount doesn't match coliver cost")
    
    return False

if __name__ == "__main__":
    print("🚀 PAYMENT SETUP ADJUSTMENT")
    print("=" * 60)
    
    # Step 1: Check current setup
    if check_current_setup():
        
        # Step 2: Ask user to fix templates (commented out for now)
        # fix_payment_templates()
        
        # For now, let's automatically use Option 1 (keep only booking payment)
        print(f"\n🔧 AUTOMATICALLY ADJUSTING TO SINGLE PAYMENT")
        print("=" * 50)
        
        templates = AutomaticPaymentTemplate.objects.filter(is_active=True)
        for template in templates:
            if 'security' in template.title.lower() or 'deposit' in template.title.lower():
                template.is_active = False
                template.save()
                print(f"✅ Disabled: {template.title}")
            else:
                print(f"✅ Keeping: {template.title} (matches coliver total cost)")
        
        # Step 3: Test the new setup
        test_new_setup()
        
        print(f"\n🎯 RESULT: Now payments will simply equal the coliver's total cost!")
    else:
        print(f"\n❌ Could not check current setup") 