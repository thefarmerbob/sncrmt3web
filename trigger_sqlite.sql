DROP TRIGGER IF EXISTS after_application_update;

CREATE TRIGGER after_application_update
AFTER UPDATE ON applications_application
FOR EACH ROW
WHEN NEW.application_status = 'Onboarding' 
     AND OLD.application_status != 'Onboarding'
     AND NOT EXISTS (
         SELECT 1 FROM colivers_coliver 
         WHERE user_id = NEW.created_by_id
     )
BEGIN
    INSERT INTO colivers_coliver (
        first_name, 
        last_name, 
        email,
        arrival_date, 
        departure_date,
        user_id, 
        chapter_name_id, 
        status, 
        created_at,
        manual_cost, 
        is_active
    )
    VALUES (
        NEW.first_name,
        NEW.last_name,
        NEW.email,
        NEW.date_join,
        NEW.date_leave,
        NEW.created_by_id,
        NEW.chapter_id,
        'ONBOARDING',
        datetime('now'),
        COALESCE(NEW.manual_cost, 0),
        1
    );
END; 