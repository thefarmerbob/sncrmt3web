#!/usr/bin/env python3
"""
Debug Django signals for automatic payment creation.
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

# Import signals manually to ensure they're loaded
import payments.signals

def test_signal_debug():
    print("🔧 Debugging Signal Handlers...")
    print("=" * 50)
    
    # Check if signals are properly imported
    print("📋 Checking signal connections...")
    from django.db.models import signals
    
    # Show connected signals for Application model
    app_receivers = signals.post_save._live_receivers(sender=Application)
    print(f"Application post_save receivers: {len(app_receivers)}")
    for receiver in app_receivers:
        print(f"  - {receiver}")
    
    # Show connected signals for Coliver model  
    coliver_receivers = signals.post_save._live_receivers(sender=Coliver)
    print(f"Coliver post_save receivers: {len(coliver_receivers)}")
    for receiver in coliver_receivers:
        print(f"  - {receiver}")
    
    print()
    
    # Test manual payment creation
    test_user, created = User.objects.get_or_create(
        username='debug_signal_user',
        defaults={
            'email': 'debugsignal@example.com',
            'first_name': 'Debug',
            'last_name': 'Signal'
        }
    )
    
    chapter = Chapter.objects.first()
    
    # Clean up
    Coliver.objects.filter(user=test_user).delete()
    Payment.objects.filter(user=test_user).delete()
    
    # Create a coliver manually
    arrival_date = date.today() + timedelta(days=30)
    departure_date = arrival_date + timedelta(days=14)
    
    coliver = Coliver.objects.create(
        user=test_user,
        first_name='Debug',
        last_name='Signal',
        email='debugsignal@example.com',
        arrival_date=arrival_date,
        departure_date=departure_date,
        chapter_name=chapter,
        status='ONBOARDING'
    )
    
    print(f"👥 Created coliver: {coliver.first_name} {coliver.last_name}")
    
    # Check if automatic payments were created by the signal
    import time
    time.sleep(0.5)
    
    payments = Payment.objects.filter(user=test_user)
    print(f"💰 Payments after coliver creation: {payments.count()}")
    
    if payments.count() == 0:
        print("❌ No automatic payments created by signal")
        
        # Try manual creation
        print("🔧 Testing manual template execution...")
        templates = AutomaticPaymentTemplate.objects.filter(is_active=True, applies_to_all_colivers=True)
        
        for template in templates:
            print(f"📋 Processing template: {template.title}")
            payment = template.create_payment_for_coliver(coliver)
            if payment:
                print(f"✅ Manual creation successful: ₩{payment.amount:,.2f}")
            else:
                print("❌ Manual creation failed")
    
    print("=" * 50)
    print("🏁 Debug completed!")

if __name__ == "__main__":
    test_signal_debug() 