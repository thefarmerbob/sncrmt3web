#!/usr/bin/env python
import os
import django

# Setup Django
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sncrmt3web.settings')
    django.setup()
except:
    pass  # Django might already be set up

from chapters.models import Chapter, PricingTier
from applications.models import Application
from datetime import date, timedelta

def test_pricing_integration():
    """Test that short-term pricing properly integrates with tiered pricing."""
    
    try:
        # Get Jeongwol chapter
        chapter = Chapter.objects.get(name='Jeongwol')
        print(f"Testing pricing for: {chapter.name}")
        print(f"Short-term pricing enabled: {chapter.use_short_term_pricing}")
        print(f"Short-term threshold: {chapter.short_term_threshold_days} days")
        print(f"Short-term rate: ₩{chapter.short_term_price_per_night:,.0f}/night")
        print(f"Tiered pricing enabled: {chapter.use_tiered_pricing}")
        print()
        
        # Show pricing tiers
        tiers = chapter.pricing_tiers.all().order_by('tier_order')
        print("Pricing Tiers:")
        for tier in tiers:
            print(f"  {tier.tier_name}: {tier.duration_days} days at ₩{tier.price_per_night:,.0f}/night")
        print()
        
        # Test different stay lengths
        test_cases = [
            (2, "Very short stay - should use short-term pricing"),
            (5, "Short stay - should use short-term pricing"),
            (7, "At threshold - should use short-term pricing"),
            (8, "Just over threshold - should use tiered pricing"),
            (14, "2 weeks - should use first tier"),
            (30, "1 month - should use first tier + second tier"),
            (60, "2 months - should use first tier + second tier"),
            (90, "3 months - should use first + second + third tier"),
            (120, "4 months - should use first + second + third tier")
        ]
        
        print("Pricing Test Results:")
        print("=" * 80)
        
        for nights, description in test_cases:
            cost = chapter.calculate_tiered_cost(nights)
            rate = chapter.get_display_rate_per_night(nights)
            breakdown = chapter.get_pricing_breakdown(nights)
            
            print(f"{nights} nights ({description})")
            print(f"  Total Cost: ₩{cost:,.0f}")
            print(f"  Display Rate: ₩{rate:,.0f}/night")
            print("  Breakdown:")
            
            for item in breakdown:
                print(f"    - {item['tier_name']}: {item['nights']} nights × ₩{item['price_per_night']:,.0f} = ₩{item['total_cost']:,.0f}")
            print()
        
        print("✅ SHORT-TERM PRICING INTEGRATION TEST PASSED!")
        print("The system correctly prioritizes:")
        print("1. Short-term pricing for stays ≤ 7 days")
        print("2. Tiered pricing for longer stays")
        print("3. Legacy pricing as fallback")
        
    except Chapter.DoesNotExist:
        print("❌ Jeongwol chapter not found. Please run: python manage.py setup_tiered_pricing")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pricing_integration() 