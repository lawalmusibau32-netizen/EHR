-- Patient management queries for the EHR module
-- These are reference statements aligned with the Python repository layer.

-- Search/list active patients
SELECT
    p.patient_id,
    p.mrn,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.sex,
    p.phone_number,
    p.email,
    p.address_line1,
    p.address_line2,
    p.city,
    p.region,
    p.country,
    p.is_active,
    p.created_at,
    p.updated_at,
    COUNT(DISTINCT mr.record_id) AS record_count,
    COUNT(DISTINCT a.appointment_id) AS appointment_count
FROM patients p
LEFT JOIN medical_records mr ON mr.patient_id = p.patient_id
LEFT JOIN appointments a ON a.patient_id = p.patient_id
WHERE (
    :search IS NULL
    OR LOWER(p.mrn) LIKE LOWER(:search_like)
    OR LOWER(p.first_name) LIKE LOWER(:search_like)
    OR LOWER(p.last_name) LIKE LOWER(:search_like)
    OR LOWER(p.email) LIKE LOWER(:search_like)
    OR LOWER(p.phone_number) LIKE LOWER(:search_like)
)
AND (:active_only = 0 OR p.is_active = 'Y')
GROUP BY
    p.patient_id, p.mrn, p.first_name, p.last_name, p.date_of_birth, p.sex,
    p.phone_number, p.email, p.address_line1, p.address_line2, p.city, p.region,
    p.country, p.is_active, p.created_at, p.updated_at
ORDER BY p.last_name, p.first_name;

-- View patient profile
SELECT
    p.patient_id,
    p.mrn,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.sex,
    p.phone_number,
    p.email,
    p.address_line1,
    p.address_line2,
    p.city,
    p.region,
    p.country,
    p.is_active,
    p.created_at,
    p.updated_at
FROM patients p
WHERE p.patient_id = :patient_id;

-- Add patient
INSERT INTO patients (
    mrn, first_name, last_name, date_of_birth, sex, phone_number, email,
    address_line1, address_line2, city, region, country, is_active, created_at, updated_at
) VALUES (
    :mrn, :first_name, :last_name, :date_of_birth, :sex, :phone_number, :email,
    :address_line1, :address_line2, :city, :region, :country, 'Y', SYSTIMESTAMP, SYSTIMESTAMP
);

-- Edit patient
UPDATE patients
SET
    mrn = :mrn,
    first_name = :first_name,
    last_name = :last_name,
    date_of_birth = :date_of_birth,
    sex = :sex,
    phone_number = :phone_number,
    email = :email,
    address_line1 = :address_line1,
    address_line2 = :address_line2,
    city = :city,
    region = :region,
    country = :country,
    is_active = :is_active,
    updated_at = SYSTIMESTAMP
WHERE patient_id = :patient_id;

-- Soft delete patient
UPDATE patients
SET is_active = 'N', updated_at = SYSTIMESTAMP
WHERE patient_id = :patient_id;

