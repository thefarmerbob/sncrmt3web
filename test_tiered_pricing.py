#!/usr/bin/env python
"""
Test script to demonstrate tiered pricing system for coliver stays.
Run this with: python manage.py shell < test_tiered_pricing.py
"""

from chapters.models import Chapter, PricingTier
from colivers.models import Coliver
from applications.models import Application
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal

print("=== Tiered Pricing System Test (with Short-term Pricing) ===\n")

# Get the Jeongwol chapter with tiered pricing
try:
    chapter = Chapter.objects.get(name='Jeongwol')
    print(f"Testing with chapter: {chapter.name}")
    print(f"Tiered pricing enabled: {chapter.use_tiered_pricing}")
    print(f"Short-term pricing enabled: {chapter.use_short_term_pricing}")
    if chapter.use_short_term_pricing:
        print(f"Short-term threshold: {chapter.short_term_threshold_days} days")
        print(f"Short-term price: ₩{chapter.short_term_price_per_night:,.0f}/night")
    print(f"Legacy cost per night: ₩{chapter.cost_per_night:,.0f}")
    print()
    
    # Show pricing tiers
    print("Pricing Tiers:")
    for tier in chapter.pricing_tiers.all():
        print(f"  {tier.tier_order}. {tier.tier_name}: ₩{tier.price_per_night:,.0f}/night for {tier.duration_days} days")
    print()
    
    # Test different stay durations including short-term
    test_durations = [3, 5, 7, 10, 14, 30, 60, 84, 90, 120, 180]
    
    print("Cost Calculations for Different Stay Durations:")
    print("-" * 70)
    print(f"{'Days':<6} {'Nights':<8} {'Total Cost':<15} {'Avg/Night':<12} {'Pricing Type':<15}")
    print("-" * 70)
    
    for days in test_durations:
        total_cost = chapter.calculate_tiered_cost(days)
        avg_per_night = total_cost / days if days > 0 else 0
        
        # Determine pricing type
        if (chapter.use_short_term_pricing and 
            days <= chapter.short_term_threshold_days and 
            chapter.short_term_price_per_night > 0):
            pricing_type = "Short-term"
        elif chapter.use_tiered_pricing and chapter.pricing_tiers.exists():
            pricing_type = "Tiered"
        else:
            pricing_type = "Legacy"
            
        print(f"{days:<6} {days:<8} ₩{total_cost:>12,.0f} ₩{avg_per_night:>9,.0f} {pricing_type:<15}")
    
    print()
    
    # Show detailed breakdown for different stay types
    test_cases = [
        (5, "5-day short stay"),
        (10, "10-day stay (beyond short-term threshold)"),
        (90, "90-day long stay")
    ]
    
    for days, description in test_cases:
        print(f"Detailed Breakdown for {description}:")
        breakdown = chapter.get_pricing_breakdown(days)
        total = Decimal('0.00')
        
        for tier in breakdown:
            tier_total = tier['total_cost']
            total += tier_total
            print(f"  {tier['tier_name']}: {tier['nights']} nights × ₩{tier['price_per_night']:,.0f} = ₩{tier_total:,.0f}")
        
        print(f"  Total: ₩{total:,.0f}")
        print()
    
    # Test with a sample coliver for short-term stay
    print("Testing with Sample Short-term Coliver:")
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='test_short_term_coliver',
            defaults={'email': 'shortterm@example.com'}
        )
        
        # Create a sample coliver with a 5-day stay
        arrival = date.today()
        departure = arrival + timedelta(days=5)
        
        # Check if coliver already exists
        coliver = Coliver.objects.filter(user=user, chapter_name=chapter).first()
        if not coliver:
            coliver = Coliver.objects.create(
                first_name='Short',
                last_name='Stay',
                email='shortterm@example.com',
                arrival_date=arrival,
                departure_date=departure,
                user=user,
                chapter_name=chapter,
                status='COLIVING'
            )
        else:
            # Update existing coliver
            coliver.arrival_date = arrival
            coliver.departure_date = departure
            coliver.save()
        
        print(f"Coliver: {coliver.first_name} {coliver.last_name}")
        print(f"Stay: {coliver.arrival_date} to {coliver.departure_date} ({(coliver.departure_date - coliver.arrival_date).days} days)")
        print(f"Chapter: {coliver.chapter_name.name}")
        print(f"Total Cost: {coliver.total_cost}")
        print()
        
        # Show pricing breakdown
        breakdown_data = coliver.get_pricing_breakdown()
        print("Pricing Breakdown:")
        for tier in breakdown_data['tiers']:
            print(f"  {tier['tier_name']}: {tier['nights']} nights × ₩{tier['price_per_night']:,.0f} = ₩{tier['total_cost']:,.0f}")
        print(f"Final Total: ₩{breakdown_data['final_total']:,.0f}")
        print()
        
    except Exception as e:
        print(f"Error creating test coliver: {e}")
    
except Chapter.DoesNotExist:
    print("Jeongwol chapter not found. Please run: python manage.py setup_tiered_pricing")

print("\n=== Test Complete ===") 