# Stay Duration Warning System

## Overview
The stay duration warning system now allows administrators to configure both minimum and maximum day thresholds that trigger warning messages when users select stay durations outside these bounds.

## What Changed

### 1. Model Updates
- Added `minimum_days` field to the `ShortStayWarning` model (default: 28 days)
- Added `maximum_days` field for upper bound warnings (default: 93 days)
- Added `long_stay_title`, `long_stay_message`, and `long_stay_button_text` fields for customizing upper bound warnings
- All fields include helpful admin text explaining their purpose

### 2. Admin Interface
- Added all new fields to the admin interface with organized fieldsets
- **Short Stay Warning (Lower Bound)** section for minimum threshold settings
- **Long Stay Warning (Upper Bound)** section for maximum threshold settings
- **General Settings** section for activation controls
- Both thresholds appear in the list view for easy overview

### 3. Frontend Updates
- Updated JavaScript in both `new_application.html` and `edit_application.html`
- JavaScript now reads both minimum and maximum threshold values from data attributes
- Added separate warning containers for short and long stay warnings
- Warnings are mutually exclusive - only one shows at a time
- Removed all hardcoded limits

### 4. Database Migration
- Created migration `0012_shortstaywarning_long_stay_button_text_and_more.py`
- Safely adds all new fields with appropriate default values

## How to Use

### For Administrators:
1. Go to Django Admin → Applications → Short Stay Warning Messages
2. Edit the active warning message
3. **Short Stay Settings:**
   - Set "Minimum days" field (e.g., 14, 21, 28)
   - Customize title, message, and button text for short stays
4. **Long Stay Settings:**
   - Set "Maximum days" field (e.g., 84, 93, 120)
   - Customize title, message, and button text for long stays
5. Save the changes

### For Users:
- **Short stay warning** appears when selecting a duration below the minimum threshold
- **Long stay warning** appears when selecting a duration above the maximum threshold
- **No warning** appears for stays within the configured bounds
- Only one warning shows at a time
- Same user experience - warnings look and behave identically

## Technical Implementation

### Model
```python
class ShortStayWarning(models.Model):
    # Short stay (lower bound) fields
    title = models.CharField(max_length=200, default="Stay Duration Notice")
    message = models.TextField(default="...")
    button_text = models.CharField(max_length=50, default="I understand, continue anyway")
    minimum_days = models.PositiveIntegerField(default=28, help_text="...")
    
    # Long stay (upper bound) fields
    maximum_days = models.PositiveIntegerField(default=93, help_text="...")
    long_stay_title = models.CharField(max_length=200, default="Extended Stay Notice")
    long_stay_message = models.TextField(default="...")
    long_stay_button_text = models.CharField(max_length=50, default="I understand, continue anyway")
```

### Template Integration
```html
<form ... data-minimum-days="{{ short_stay_message.minimum_days|default:28 }}" 
           data-maximum-days="{{ short_stay_message.maximum_days|default:93 }}">

<!-- Short Stay Warning Container -->
<div id="stayWarningMessage" class="hidden">...</div>

<!-- Long Stay Warning Container -->
<div id="longStayWarningMessage" class="hidden">...</div>
```

### JavaScript
```javascript
const minimumDays = parseInt(document.getElementById('applicationForm').getAttribute('data-minimum-days')) || 28;
const maximumDays = parseInt(document.getElementById('applicationForm').getAttribute('data-maximum-days')) || 93;

if (daysDifference < minimumDays) {
    // Show short stay warning
} else if (daysDifference > maximumDays) {
    // Show long stay warning
}
```

## Testing
- All functionality has been tested and verified
- Comprehensive test suite covers both bounds and edge cases
- Backward compatibility maintained
- Default behavior unchanged if no configuration is made

## Example Scenarios

### Scenario 1: Conservative Settings
- **Minimum:** 21 days (3 weeks)
- **Maximum:** 84 days (12 weeks)
- **Result:** Encourages 3-week to 3-month stays

### Scenario 2: Flexible Settings  
- **Minimum:** 14 days (2 weeks)
- **Maximum:** 120 days (4 months)
- **Result:** Allows wider range of stay durations

### Scenario 3: Strict Settings
- **Minimum:** 30 days (1 month)
- **Maximum:** 60 days (2 months)
- **Result:** Enforces specific stay duration range

## Benefits
- **Dual Control**: Manage both minimum and maximum stay durations
- **Flexibility**: Admins can adjust both thresholds independently
- **Custom Messaging**: Different messages for short vs. long stay warnings
- **No Code Changes**: All threshold and message changes via admin interface
- **Backward Compatible**: Existing installations continue to work with defaults
- **User-Friendly**: Clear admin interface with organized sections
- **Consistent UX**: Both warnings use identical styling and behavior 