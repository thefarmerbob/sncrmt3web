DELIMITER $$

CREATE TRIGGER after_application_update
AFTER UPDATE ON applications_application
FOR EACH ROW
BEGIN
    IF NEW.application_status = 'ONBOARDING' AND OLD.application_status != 'ONBOARDING' THEN
        INSERT INTO colivers_coliver (
            first_name, last_name, email,
            arrival_date, departure_date,
            user_id, chapter_name_id, 
            status, created_at, manual_cost,
            is_active
        )
        SELECT 
            NEW.first_name,
            NEW.last_name,
            NEW.email,
            NEW.date_join,
            NEW.date_leave,
            created_by_id,
            c.id,
            'ONBOARDING',
            NOW(),
            NEW.manual_cost,
            1  -- Set is_active to true by default
        FROM chapters_chapter AS c
        WHERE c.id = NEW.chapter_id;
    END IF;
END $$

DELIMITER ; 