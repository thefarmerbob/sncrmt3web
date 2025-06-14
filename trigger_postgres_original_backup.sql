CREATE OR REPLACE FUNCTION after_application_update_fn()
RETURNS TRIGGER AS $$
DECLARE
    coliver_id INT;
    coliver_exists INT := 0;
    chapter_id INT;
    cost_per_night NUMERIC(10,2);
    total_cost NUMERIC(10,2);
    security_deposit_amount NUMERIC(10,2) := 100000.00;
    arrival_date DATE;
    departure_date DATE;
    security_due_date DATE;
    booking_due_date DATE;
    chapter_name TEXT;
    security_payment_id INT;
    booking_payment_id INT;
BEGIN
    IF NEW.application_status = 'Onboarding' AND OLD.application_status != 'Onboarding' THEN
        
        -- Check if coliver already exists
        SELECT COUNT(*) INTO coliver_exists 
        FROM colivers_coliver 
        WHERE user_id = NEW.created_by_id;

        -- Get chapter info
        SELECT id, name, cost_per_night INTO chapter_id, chapter_name, cost_per_night
        FROM chapters_chapter 
        WHERE id = NEW.chapter_id;

        arrival_date := NEW.date_join;
        departure_date := NEW.date_leave;
        security_due_date := arrival_date - INTERVAL '7 days';
        booking_due_date := arrival_date;

        -- Calculate total cost
        total_cost := EXTRACT(DAY FROM departure_date - arrival_date) * cost_per_night;

        -- Create or update coliver
        IF coliver_exists = 0 THEN
            INSERT INTO colivers_coliver (
                first_name, last_name, email,
                arrival_date, departure_date,
                user_id, chapter_name_id, 
                status, created_at,
                manual_cost, is_active
            )
            VALUES (
                NEW.first_name,
                NEW.last_name,
                NEW.email,
                NEW.date_join,
                NEW.date_leave,
                NEW.created_by_id,
                chapter_id,
                'ONBOARDING',
                NOW(),
                0,
                TRUE
            )
            RETURNING id INTO coliver_id;
        ELSE
            SELECT id INTO coliver_id 
            FROM colivers_coliver 
            WHERE user_id = NEW.created_by_id 
            LIMIT 1;
        END IF;

        -- Create Security Deposit Payment
        INSERT INTO payments_payment (
            user_id,
            description,
            amount,
            due_date,
            status,
            created_at,
            modified_at,
            payment_type,
            is_automatic
        ) VALUES (
            NEW.created_by_id,
            'Security deposit for ' || NEW.first_name || ' ' || NEW.last_name || ' stay at ' || chapter_name,
            security_deposit_amount,
            security_due_date,
            'requested',
            NOW(),
            NOW(),
            'security_deposit',
            TRUE
        ) RETURNING id INTO security_payment_id;

        -- Link Security Deposit to Automatic Payment
        INSERT INTO payments_automaticpayment (
            payment_id,
            template_id,
            coliver_id,
            created_at
        ) VALUES (
            security_payment_id,
            (SELECT id FROM payments_automaticpaymenttemplate WHERE title = 'Security Deposit' LIMIT 1),
            coliver_id,
            NOW()
        );

        -- Create Booking Payment
        INSERT INTO payments_payment (
            user_id,
            description,
            amount,
            due_date,
            status,
            created_at,
            modified_at,
            payment_type,
            is_automatic
        ) VALUES (
            NEW.created_by_id,
            'Full booking payment for ' || NEW.first_name || ' ' || NEW.last_name || ' stay at ' || chapter_name || 
            ' (' || NEW.date_join || ' to ' || NEW.date_leave || ')',
            total_cost,
            booking_due_date,
            'requested',
            NOW(),
            NOW(),
            'booking',
            TRUE
        ) RETURNING id INTO booking_payment_id;

        -- Link Booking Payment to Automatic Payment
        INSERT INTO payments_automaticpayment (
            payment_id,
            template_id,
            coliver_id,
            created_at
        ) VALUES (
            booking_payment_id,
            (SELECT id FROM payments_automaticpaymenttemplate WHERE title = 'Booking Payment' LIMIT 1),
            coliver_id,
            NOW()
        );

    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop and recreate trigger
DROP TRIGGER IF EXISTS after_application_update ON applications_application;

CREATE TRIGGER after_application_update
AFTER UPDATE ON applications_application
FOR EACH ROW
EXECUTE FUNCTION after_application_update_fn(); 