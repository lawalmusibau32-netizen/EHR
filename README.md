# Secure EHR System Foundation

This repository provides a modular starting point for a secure Electronic Health Record system built with:

- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
- Backend: Python Flask
- Database: Oracle Database

## What is included

- Flask application factory
- Blueprint-based module layout
- Oracle database connection configuration
- Environment variable configuration
- Bootstrap starter templates
- Static asset structure for future UI work
- Role-specific dashboards for Administrator, Doctor, Nurse, and Receptionist
- Audit logging and security monitoring dashboards
- AES-256 field encryption support for sensitive patient and clinical data
- MFA, account lockout, session timeout, CSRF checks, and secure HTTP headers
- README and installation guide

## Project structure

```text
ehr-system/
  app/
    __init__.py
    config.py
    extensions.py
    db/
      __init__.py
      oracle.py
    blueprints/
      __init__.py
      auth/
        __init__.py
        routes.py
      main/
        __init__.py
        routes.py
      appointments/
        __init__.py
        routes.py
      patients/
        __init__.py
        routes.py
    models/
      __init__.py
    repositories/
      __init__.py
      base_repository.py
      appointment_repository.py
      medical_record_repository.py
      patient_repository.py
    services/
      __init__.py
      appointment_service.py
      auth_service.py
      medical_record_service.py
      patient_service.py
    utils/
      __init__.py
      auth.py
    templates/
      base.html
      errors/
        401.html
        403.html
      auth/
        login.html
        register.html
      main/
        dashboard.html
      appointments/
        index.html
        form.html
        detail.html
      patients/
        index.html
        form.html
        profile.html
    static/
      css/
        style.css
      js/
        main.js
  .env.example
  requirements.txt
  run.py
  wsgi.py
```

## Installation guide

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and update the Oracle credentials and secret key.

### 5. Run the application

```bash
python run.py
```

The app will start in development mode using the Flask development server.

## Oracle database setup

This foundation uses `python-oracledb` with environment-driven connection settings.

Recommended variables:

- `ORACLE_HOST`
- `ORACLE_PORT`
- `ORACLE_SERVICE_NAME`
- `ORACLE_USERNAME`
- `ORACLE_PASSWORD`
- `ORACLE_MIN_POOL`
- `ORACLE_MAX_POOL`
- `ORACLE_INCREMENT`
- `EHR_ENCRYPTION_KEY`
- `ACCOUNT_LOCKOUT_ATTEMPTS`
- `ACCOUNT_LOCKOUT_MINUTES`
- `SESSION_TIMEOUT_MINUTES`

Generate an AES-256 encryption key for `EHR_ENCRYPTION_KEY`:

```bash
python -c "from app.utils.crypto import generate_encryption_key; print(generate_encryption_key())"
```

## Authentication

The auth module uses:

- bcrypt password hashing
- JWT access tokens in secure HttpOnly cookies
- server-side auth session records for revocation
- CSRF tokens for form-based login, registration, and logout
- optional TOTP-style MFA
- account lockout after repeated failed login attempts
- session timeout enforcement
- secure HTTP headers including CSP, frame protection, content-type protection, referrer policy, and production HSTS
- browser routes for `/auth/register`, `/auth/login`, and `/auth/logout`
- API routes for `/auth/api/register`, `/auth/api/login`, `/auth/api/me`, and `/auth/api/logout`

## Audit logging and monitoring

Audit logs are stored in Oracle and include user ID, timestamp, IP address, action type, entity, entity ID, and action details. The audit dashboard is available to administrators at `/audit-logs`.

The security monitoring dashboard at `/security-monitoring` includes failed login monitoring, locked accounts, recent security events, user activity analytics, and Chart.js visualizations.

## Data encryption

Sensitive patient fields and clinical diagnosis, prescription, and treatment fields are encrypted before database storage with AES-256-GCM. Values are decrypted by the application service layer for authorized users. Existing legacy plaintext values remain readable so development seed data and pre-encryption rows can still be viewed.

## Role-based access

Supported roles:

- Administrator
- Doctor
- Nurse
- Receptionist

Access is enforced at the route layer and on API endpoints. Dashboard content changes based on the signed-in role, and unauthorized access returns a 401 or 403 response depending on whether the request is unauthenticated or blocked by role policy.

## Oracle SQL scripts

Database scripts are stored in [`db/`](</c:/Users/lawal/Desktop/EHR/db>):

- `01_schema.sql` creates the tables, keys, constraints, and indexes
- `02_seed_data.sql` inserts sample data
- `03_run_all.sql` runs schema plus seed data in order
- `04_drop_schema.sql` removes the schema objects
- `05_patient_module.sql` contains patient module query references
- `06_appointment_module.sql` contains appointment module query references
- `07_security_module.sql` upgrades existing databases with MFA, lockout, audit, and clinical child-table support

Run them with SQL*Plus or SQLcl:

```sql
@db/03_run_all.sql
```

For an existing database created before the security phases, run:

```sql
@db/07_security_module.sql
```

## Vercel deployment

This project is configured for Vercel as a Flask app with `wsgi.py` as the entrypoint. Deploy from the repository root with the included `vercel.json`.

Set the following environment variables in Vercel before deploying:

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `EHR_ENCRYPTION_KEY`
- `ORACLE_HOST`
- `ORACLE_PORT`
- `ORACLE_SERVICE_NAME`
- `ORACLE_USERNAME`
- `ORACLE_PASSWORD`

The Oracle database must be reachable from Vercel's runtime network. If the database is private, expose it through a secure network path that allows outbound connections from the function runtime.

## Next steps

The scaffold is ready for:

- authentication and role-based access control
- patient demographics
- encounters and clinical notes
- audit logging
- lab and medication modules
- document uploads
- encryption and key management
