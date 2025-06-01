-- Drop existing trigger
DROP TRIGGER IF EXISTS after_application_update;

-- Create comprehensive trigger that handles both coliver and payment creation
DELIMITER //

CREATE TRIGGER after_application_update
AFTER UPDATE ON applications_application
FOR EACH ROW
BEGIN
    DECLARE coliver_id INT;
    DECLARE coliver_exists INT DEFAULT 0;
    DECLARE chapter_id INT;
    DECLARE total_cost DECIMAL(10,2);
    DECLARE security_deposit_amount DECIMAL(10,2) DEFAULT 100000.00;
    DECLARE arrival_date DATE;
    DECLARE departure_date DATE;
    DECLARE security_due_date DATE;
    DECLARE booking_due_date DATE;
    
    -- Only proceed if status changed TO 'Onboarding' FROM something else
    IF NEW.application_status = 'Onboarding' AND OLD.application_status != 'Onboarding' THEN
        
        -- Check if coliver already exists for this user
        SELECT COUNT(*) INTO coliver_exists 
        FROM colivers_coliver 
        WHERE user_id = NEW.created_by_id;
        
        -- Get chapter info and calculate dates
        SELECT c.id INTO chapter_id
        FROM chapters_chapter c 
        WHERE c.id = NEW.chapter_id;
        
        SET arrival_date = NEW.date_join;
        SET departure_date = NEW.date_leave;
        SET security_due_date = DATE_SUB(arrival_date, INTERVAL 7 DAY);
        SET booking_due_date = arrival_date;
        
        -- Calculate total cost (days * daily_rate)
        SELECT 
            DATEDIFF(NEW.date_leave, NEW.date_join) * c.daily_rate INTO total_cost
        FROM chapters_chapter c 
        WHERE c.id = NEW.chapter_id;
        
        -- Create or update coliver
        IF coliver_exists = 0 THEN
            INSERT INTO colivers_coliver (
                first_name, last_name, email,
                arrival_date, departure_date,
                user_id, chapter_name_id, 
                status, created_at, modified_at,
                manual_cost, total_cost, is_active
            )
            SELECT 
                NEW.first_name,
                NEW.last_name,
                NEW.email,
                NEW.date_join,
                NEW.date_leave,
                NEW.created_by_id,
                c.id,
                'ONBOARDING',
                NOW(),
                NOW(),
                0,
                total_cost,
                1
            FROM chapters_chapter c 
            WHERE c.id = NEW.chapter_id;
            
            SET coliver_id = LAST_INSERT_ID();
        ELSE
            -- Get existing coliver ID
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
            CONCAT('Security deposit for ', NEW.first_name, ' ', NEW.last_name, ' stay at ', 
                   (SELECT name FROM chapters_chapter WHERE id = NEW.chapter_id)),
            security_deposit_amount,
            security_due_date,
            'requested',
            NOW(),
            NOW(),
            'security_deposit',
            1
        );
        
        -- Create Security Deposit AutomaticPayment link
        INSERT INTO payments_automaticpayment (
            payment_id,
            template_id,
            coliver_id,
            created_at
        ) VALUES (
            LAST_INSERT_ID(),
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
            CONCAT('Full booking payment for ', NEW.first_name, ' ', NEW.last_name, ' stay at ', 
                   (SELECT name FROM chapters_chapter WHERE id = NEW.chapter_id), 
                   ' (', NEW.date_join, ' to ', NEW.date_leave, ')'),
            total_cost,
            booking_due_date,
            'requested',
            NOW(),
            NOW(),
            'booking',
            1
        );
        
        -- Create Booking Payment AutomaticPayment link
        INSERT INTO payments_automaticpayment (
            payment_id,
            template_id,
            coliver_id,
            created_at
        ) VALUES (
            LAST_INSERT_ID(),
            (SELECT id FROM payments_automaticpaymenttemplate WHERE title = 'Booking Payment' LIMIT 1),
            coliver_id,
            NOW()
        );
        
    END IF;
END//

DELIMITER ; 