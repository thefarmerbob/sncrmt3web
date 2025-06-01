# Automatic Payment System Guide

## Overview

The automatic payment system allows admins to set up payment templates that automatically create payments for colivers based on configurable rules. This system supports flexible date scheduling and amount calculation.

## Features

### 1. Automatic Payment Templates
- **Flexible Date Scheduling**: Choose when payments are due relative to arrival/departure dates
- **Multiple Amount Types**: Fixed amounts, full stay cost, or percentage of stay cost
- **Editable Titles & Descriptions**: Customize payment descriptions with dynamic variables
- **Enable/Disable Templates**: Turn templates on/off as needed

### 2. Date Configuration Options
- **Arrival Date**: Payment due on coliver's arrival date
- **Departure Date**: Payment due on coliver's departure date  
- **Custom Offset**: Payment due X days before/after arrival date (negative for before, positive for after)

### 3. Amount Configuration Options
- **Fixed Amount**: Set a specific amount (e.g., ₩100,000 security deposit)
- **Total Stay Cost**: Payment equals the full calculated cost of the coliver's stay
- **Percentage of Total Cost**: Payment equals a percentage of the stay cost (e.g., 50% upfront)

## How to Use

### Setting Up Templates

1. **Access Admin Interface**:
   - Go to Django Admin → Payments → Automatic payment templates

2. **Create or Edit Templates**:
   - **Title**: Name for the payment (e.g., "Booking Payment", "Security Deposit")
   - **Description Template**: Use variables like `{coliver_name}`, `{chapter_name}`, `{arrival_date}`, `{departure_date}`
   - **Date Type**: Choose arrival_date, departure_date, or custom_offset
   - **Days Offset**: Number of days to add/subtract from base date
   - **Amount Type**: Choose fixed, total_cost, or percentage_cost
   - **Is Active**: Enable/disable the template
   - **Applies to All Colivers**: Should this template create payments for all colivers

### Default Templates Created

The system comes with these default templates:

1. **Booking Payment** (Active)
   - Amount: Full stay cost
   - Due: On arrival date
   - Description: "Full booking payment for {coliver_name} stay at {chapter_name} ({arrival_date} to {departure_date})"

2. **Security Deposit** (Active)
   - Amount: ₩100,000 (fixed)
   - Due: 7 days before arrival
   - Description: "Security deposit for {coliver_name} stay at {chapter_name}"

3. **Upfront Payment (50%)** (Disabled by default)
   - Amount: 50% of stay cost
   - Due: 14 days before arrival
   - Description: "50% upfront payment for {coliver_name} booking at {chapter_name}"

4. **Checkout Payment** (Disabled by default)
   - Amount: ₩50,000 (fixed)
   - Due: On departure date
   - Description: "Final checkout payment for {coliver_name} at {chapter_name}"

### Generating Payments

#### For New Colivers
- Payments are **automatically created** when new colivers are added to the system
- Only active templates that apply to all colivers will generate payments

#### For Existing Colivers
- Use the **"Generate Payments" button** in the admin interface for each template
- Or run the management command: `python manage.py generate_payments_for_existing_colivers`

#### Command Line Options
```bash
# Dry run (see what would be created)
python manage.py generate_payments_for_existing_colivers --dry-run

# Generate for specific template only
python manage.py generate_payments_for_existing_colivers --template-id 1

# Generate for all active templates
python manage.py generate_payments_for_existing_colivers
```

### Viewing Automatic Payments

1. **In Payments List**: 
   - Automatic payments show "✓" in the "Auto" column
   - Manual payments show "✗" in the "Auto" column

2. **Automatic Payments Section**:
   - View all automatic payments and their associated templates
   - Read-only interface showing the relationship between templates and generated payments

## Admin Workflow Examples

### Example 1: Setting Up a Security Deposit
1. Create template with title "Security Deposit"
2. Set amount type to "Fixed Amount" with ₩100,000
3. Set date type to "Arrival Date" with -7 days offset (due 7 days before arrival)
4. Enable the template
5. Use "Generate Payments" to create for existing colivers

### Example 2: Setting Up a 30% Upfront Payment
1. Create template with title "Upfront Payment (30%)"
2. Set amount type to "Percentage of Total Cost" with 30%
3. Set date type to "Arrival Date" with -14 days offset (due 2 weeks before arrival)
4. Enable the template
5. Use "Generate Payments" to create for existing colivers

### Example 3: Editing Payment Dates
Admins can edit the title and due date of any payment (automatic or manual) in the regular Payments admin interface. The system maintains the link to the original template for tracking purposes.

## Technical Notes

- Automatic payments are created when colivers are added or when key fields (dates, chapter, cost) are updated
- Templates can be safely disabled without affecting existing payments
- Each coliver can only have one payment per template (duplicates are prevented)
- Payments are recalculated if coliver details change (only for payments in 'requested' status)

## Management Commands

### Setup Default Templates
```bash
python manage.py setup_default_payment_templates
```

### Generate Payments for Existing Colivers
```bash
# See what would be created
python manage.py generate_payments_for_existing_colivers --dry-run

# Create payments
python manage.py generate_payments_for_existing_colivers
``` 