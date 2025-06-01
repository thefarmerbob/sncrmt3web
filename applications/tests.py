from django.test import TestCase
from .models import ShortStayWarning

# Create your tests here.

class ShortStayWarningTestCase(TestCase):
    def test_default_minimum_days(self):
        """Test that the default minimum_days is 28"""
        warning = ShortStayWarning.objects.create(
            title="Test Warning",
            message="Test message",
            button_text="Test button"
        )
        self.assertEqual(warning.minimum_days, 28)
    
    def test_default_maximum_days(self):
        """Test that the default maximum_days is 93"""
        warning = ShortStayWarning.objects.create(
            title="Test Warning",
            message="Test message",
            button_text="Test button"
        )
        self.assertEqual(warning.maximum_days, 93)
    
    def test_custom_minimum_days(self):
        """Test that custom minimum_days can be set"""
        warning = ShortStayWarning.objects.create(
            title="Test Warning",
            message="Test message", 
            button_text="Test button",
            minimum_days=14
        )
        self.assertEqual(warning.minimum_days, 14)
    
    def test_custom_maximum_days(self):
        """Test that custom maximum_days can be set"""
        warning = ShortStayWarning.objects.create(
            title="Test Warning",
            message="Test message", 
            button_text="Test button",
            maximum_days=120
        )
        self.assertEqual(warning.maximum_days, 120)
    
    def test_long_stay_default_fields(self):
        """Test that long stay fields have correct defaults"""
        warning = ShortStayWarning.objects.create(
            title="Test Warning",
            message="Test message",
            button_text="Test button"
        )
        self.assertEqual(warning.long_stay_title, "Extended Stay Notice")
        self.assertEqual(warning.long_stay_message, "Please note that initial bookings are limited to 3 months. You can extend your stay after arrival if space is available.")
        self.assertEqual(warning.long_stay_button_text, "I understand, continue anyway")
    
    def test_custom_long_stay_fields(self):
        """Test that custom long stay fields can be set"""
        warning = ShortStayWarning.objects.create(
            title="Test Warning",
            message="Test message",
            button_text="Test button",
            long_stay_title="Custom Long Stay Title",
            long_stay_message="Custom long stay message",
            long_stay_button_text="Custom button text"
        )
        self.assertEqual(warning.long_stay_title, "Custom Long Stay Title")
        self.assertEqual(warning.long_stay_message, "Custom long stay message")
        self.assertEqual(warning.long_stay_button_text, "Custom button text")
    
    def test_get_active_with_all_fields(self):
        """Test that get_active returns all fields correctly"""
        # Create an active warning with custom values
        warning = ShortStayWarning.objects.create(
            title="Active Warning",
            message="Active message",
            button_text="Active button",
            minimum_days=21,
            maximum_days=120,
            long_stay_title="Custom Long Title",
            long_stay_message="Custom long message",
            long_stay_button_text="Custom long button",
            is_active=True
        )
        
        active_warning = ShortStayWarning.get_active()
        self.assertEqual(active_warning.minimum_days, 21)
        self.assertEqual(active_warning.maximum_days, 120)
        self.assertEqual(active_warning.long_stay_title, "Custom Long Title")
        self.assertEqual(active_warning.long_stay_message, "Custom long message")
        self.assertEqual(active_warning.long_stay_button_text, "Custom long button")
    
    def test_get_active_default_when_none_exists(self):
        """Test that get_active returns default values when no warning exists"""
        # Ensure no warnings exist
        ShortStayWarning.objects.all().delete()
        
        active_warning = ShortStayWarning.get_active()
        self.assertEqual(active_warning.minimum_days, 28)
        self.assertEqual(active_warning.maximum_days, 93)
        self.assertEqual(active_warning.long_stay_title, "Extended Stay Notice")
        self.assertEqual(active_warning.long_stay_message, "Please note that initial bookings are limited to 3 months. You can extend your stay after arrival if space is available.")
        self.assertEqual(active_warning.long_stay_button_text, "I understand, continue anyway")
    
    def test_only_one_active_warning(self):
        """Test that only one warning can be active at a time"""
        # Create first active warning
        warning1 = ShortStayWarning.objects.create(
            title="Warning 1",
            message="Message 1",
            button_text="Button 1",
            minimum_days=14,
            maximum_days=60,
            is_active=True
        )
        
        # Create second active warning
        warning2 = ShortStayWarning.objects.create(
            title="Warning 2", 
            message="Message 2",
            button_text="Button 2",
            minimum_days=30,
            maximum_days=120,
            is_active=True
        )
        
        # Refresh from database
        warning1.refresh_from_db()
        warning2.refresh_from_db()
        
        # Only the second warning should be active
        self.assertFalse(warning1.is_active)
        self.assertTrue(warning2.is_active)
        
        # get_active should return the second warning
        active_warning = ShortStayWarning.get_active()
        self.assertEqual(active_warning.id, warning2.id)
        self.assertEqual(active_warning.minimum_days, 30)
        self.assertEqual(active_warning.maximum_days, 120)
