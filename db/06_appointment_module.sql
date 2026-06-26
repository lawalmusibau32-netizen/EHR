-- Appointment management queries for the EHR module
-- These are reference statements aligned with the Python repository layer.




-- View/search appointments
SELECT
    a.appointment_id,
    a.patient_id,
    a.scheduled_by_user_id,
    a.clinician_user_id,
    a.appointment_date,
    a.appointment_type,
    a.status,
    a.reason,
    a.location,
    LEFT(a.notes::text, 4000) AS notes,
    p.mrn,
    p.first_name AS patient_first_name,
    p.last_name AS patient_last_name,
    scheduler.display_name AS scheduled_by_name,
    clinician.display_name AS clinician_name
FROM appointments a
JOIN patients p ON p.patient_id = a.patient_id
JOIN users scheduler ON scheduler.user_id = a.scheduled_by_user_id
LEFT JOIN users clinician ON clinician.user_id = a.clinician_user_id
WHERE (:status IS NULL OR a.status = :status)
  AND (:patient_id IS NULL OR a.patient_id = :patient_id)
  AND (
    :search IS NULL
    OR LOWER(p.mrn) LIKE LOWER(:search_like)
    OR LOWER(p.first_name) LIKE LOWER(:search_like)
    OR LOWER(p.last_name) LIKE LOWER(:search_like)
    OR LOWER(a.appointment_type) LIKE LOWER(:search_like)
    OR LOWER(COALESCE(a.reason, ' ')) LIKE LOWER(:search_like)
    OR LOWER(COALESCE(a.location, ' ')) LIKE LOWER(:search_like)
    OR LOWER(COALESCE(clinician.display_name, ' ')) LIKE LOWER(:search_like)
  )
ORDER BY a.appointment_date DESC, a.created_at DESC;

-- View one appointment
SELECT
    a.appointment_id,
    a.patient_id,
    a.scheduled_by_user_id,
    a.clinician_user_id,
    a.appointment_date,
    a.appointment_type,
    a.status,
    a.reason,
    a.location,
    LEFT(a.notes::text, 4000) AS notes,
    p.mrn,
    p.first_name AS patient_first_name,
    p.last_name AS patient_last_name,
    p.phone_number AS patient_phone_number,
    p.email AS patient_email,
    scheduler.display_name AS scheduled_by_name,
    clinician.display_name AS clinician_name
FROM appointments a
JOIN patients p ON p.patient_id = a.patient_id
JOIN users scheduler ON scheduler.user_id = a.scheduled_by_user_id
LEFT JOIN users clinician ON clinician.user_id = a.clinician_user_id
WHERE a.appointment_id = :appointment_id;

-- Schedule appointment
INSERT INTO appointments (
    patient_id, scheduled_by_user_id, clinician_user_id, appointment_date,
    appointment_type, status, reason, location, notes, created_at, updated_at
) VALUES (
    :patient_id, :scheduled_by_user_id, :clinician_user_id, :appointment_date,
    :appointment_type, 'SCHEDULED', :reason, :location, :notes, NOW(), NOW()
);

-- Reschedule or update appointment details
UPDATE appointments
SET patient_id = :patient_id,
    clinician_user_id = :clinician_user_id,
    appointment_date = :appointment_date,
    appointment_type = :appointment_type,
    status = :status,
    reason = :reason,
    location = :location,
    notes = :notes,
    updated_at = NOW()
WHERE appointment_id = :appointment_id;

-- Cancel appointment
UPDATE appointments
SET status = 'CANCELLED',
    notes = CASE
        WHEN :cancel_note IS NULL THEN notes
        WHEN notes IS NULL THEN :cancel_note
        ELSE notes || CHR(10) || :cancel_note
    END,
    updated_at = NOW()
WHERE appointment_id = :appointment_id;

-- Appointment selectors
SELECT patient_id, mrn, first_name, last_name
FROM patients
WHERE is_active = 'Y'
ORDER BY last_name, first_name;

SELECT u.user_id, u.display_name, u.username, r.role_name
FROM users u
JOIN roles r ON r.role_id = u.role_id
WHERE u.is_active = 'Y'
  AND LOWER(r.role_name) IN ('doctor', 'administrator')
ORDER BY r.role_name, u.display_name;
