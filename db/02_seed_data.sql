-- Oracle seed data for the EHR foundation
-- Run after 01_schema.sql
-- The password_hash values below are placeholders for schema/demo loading.
-- Use the Flask registration flow to create bcrypt-backed application users.

ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD';
ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF3';

INSERT INTO roles (role_name, description, is_system) VALUES ('Administrator', 'Platform administrator', 'Y');
INSERT INTO roles (role_name, description, is_system) VALUES ('Doctor', 'Doctor or advanced practitioner', 'Y');
INSERT INTO roles (role_name, description, is_system) VALUES ('Nurse', 'Clinical support staff', 'Y');
INSERT INTO roles (role_name, description, is_system) VALUES ('Receptionist', 'Registration and scheduling staff', 'Y');

INSERT INTO users (role_id, username, display_name, email, password_hash, password_salt, is_active, last_login_at)
VALUES (
    (SELECT role_id FROM roles WHERE role_name = 'Administrator'),
    'admin',
    'System Administrator',
    'admin@healthiq.local',
    'pbkdf2$sha256$demo-admin-hash',
    'demo-salt-admin',
    'Y',
    SYSTIMESTAMP
);

INSERT INTO users (role_id, username, display_name, email, password_hash, password_salt, is_active, last_login_at)
VALUES (
    (SELECT role_id FROM roles WHERE role_name = 'Doctor'),
    'clinician',
    'Dr. Maya Clarke',
    'maya.clarke@healthiq.local',
    'pbkdf2$sha256$demo-clinician-hash',
    'demo-salt-clinician',
    'Y',
    SYSTIMESTAMP
);

INSERT INTO users (role_id, username, display_name, email, password_hash, password_salt, is_active)
VALUES (
    (SELECT role_id FROM roles WHERE role_name = 'Nurse'),
    'nurse',
    'Nurse Jordan Lee',
    'jordan.lee@healthiq.local',
    'pbkdf2$sha256$demo-nurse-hash',
    'demo-salt-nurse',
    'Y'
);

INSERT INTO users (role_id, username, display_name, email, password_hash, password_salt, is_active)
VALUES (
    (SELECT role_id FROM roles WHERE role_name = 'Receptionist'),
    'reception',
    'Grace Mensah',
    'grace.mensah@healthiq.local',
    'pbkdf2$sha256$demo-reception-hash',
    'demo-salt-reception',
    'Y'
);

INSERT INTO patients (
    mrn, first_name, last_name, date_of_birth, sex, phone_number, email,
    address_line1, city, region, country, is_active
) VALUES (
    'MRN-10001', 'Amina', 'Owusu', DATE '1987-04-13', 'Female', '+233 20 111 2233',
    'amina.owusu@example.com', '12 Airport Road', 'Accra', 'Greater Accra', 'Ghana', 'Y'
);

INSERT INTO patients (
    mrn, first_name, last_name, date_of_birth, sex, phone_number, email,
    address_line1, city, region, country, is_active
) VALUES (
    'MRN-10002', 'Kwame', 'Mensah', DATE '1979-11-29', 'Male', '+233 24 555 7788',
    'kwame.mensah@example.com', '44 Ring Road Central', 'Accra', 'Greater Accra', 'Ghana', 'Y'
);

INSERT INTO patients (
    mrn, first_name, last_name, date_of_birth, sex, phone_number, email,
    address_line1, city, region, country, is_active
) VALUES (
    'MRN-10003', 'Sarah', 'Boateng', DATE '1991-08-02', 'Female', '+233 54 222 9988',
    'sarah.boateng@example.com', '9 Kumasi Avenue', 'Kumasi', 'Ashanti', 'Ghana', 'Y'
);

INSERT INTO medical_records (
    patient_id, created_by_user_id, record_type, title, clinical_note, record_status, encounter_date
) VALUES (
    (SELECT patient_id FROM patients WHERE mrn = 'MRN-10001'),
    (SELECT user_id FROM users WHERE username = 'clinician'),
    'Encounter',
    'Initial Consultation',
    'Baseline assessment completed. Vital signs stable. Follow-up recommended in two weeks.',
    'ACTIVE',
    SYSTIMESTAMP
);

INSERT INTO medical_records (
    patient_id, created_by_user_id, record_type, title, clinical_note, record_status, encounter_date
) VALUES (
    (SELECT patient_id FROM patients WHERE mrn = 'MRN-10002'),
    (SELECT user_id FROM users WHERE username = 'clinician'),
    'Lab Result',
    'Routine Blood Panel',
    'CBC and chemistry panel reviewed. No urgent abnormalities noted.',
    'ACTIVE',
    SYSTIMESTAMP
);

INSERT INTO appointments (
    patient_id, scheduled_by_user_id, clinician_user_id, appointment_date,
    appointment_type, status, reason, location, notes
) VALUES (
    (SELECT patient_id FROM patients WHERE mrn = 'MRN-10001'),
    (SELECT user_id FROM users WHERE username = 'reception'),
    (SELECT user_id FROM users WHERE username = 'clinician'),
    SYSTIMESTAMP + NUMTODSINTERVAL(1, 'DAY') + NUMTODSINTERVAL(9, 'HOUR'),
    'Consultation',
    'SCHEDULED',
    'Annual review',
    'Room 201',
    'Bring previous lab results'
);

INSERT INTO appointments (
    patient_id, scheduled_by_user_id, clinician_user_id, appointment_date,
    appointment_type, status, reason, location, notes
) VALUES (
    (SELECT patient_id FROM patients WHERE mrn = 'MRN-10002'),
    (SELECT user_id FROM users WHERE username = 'reception'),
    (SELECT user_id FROM users WHERE username = 'clinician'),
    SYSTIMESTAMP + NUMTODSINTERVAL(1, 'DAY') + NUMTODSINTERVAL(11, 'HOUR'),
    'Follow-up',
    'CHECKED_IN',
    'Medication review',
    'Room 104',
    'Patient checked in at reception'
);

INSERT INTO audit_logs (
    user_id, action_type, entity_name, entity_id, details, ip_address, created_at
) VALUES (
    (SELECT user_id FROM users WHERE username = 'admin'),
    'LOGIN',
    'session',
    'seed-admin-session',
    'Initial administrative access for demonstration purposes.',
    '127.0.0.1',
    SYSTIMESTAMP
);

INSERT INTO audit_logs (
    user_id, action_type, entity_name, entity_id, details, ip_address, created_at
) VALUES (
    (SELECT user_id FROM users WHERE username = 'clinician'),
    'CREATE',
    'medical_records',
    '1',
    'Created first encounter record for MRN-10001.',
    '127.0.0.1',
    SYSTIMESTAMP
);

INSERT INTO audit_logs (
    user_id, action_type, entity_name, entity_id, details, ip_address, created_at
) VALUES (
    (SELECT user_id FROM users WHERE username = 'reception'),
    'CREATE',
    'appointments',
    '1',
    'Scheduled consultation for MRN-10001.',
    '127.0.0.1',
    SYSTIMESTAMP
);

COMMIT;
