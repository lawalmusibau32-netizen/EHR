# EHR

A modern Electronic Health Record system built with Next.js 16, deployed on Vercel with a Neon (PostgreSQL) database.

## System Overview

EHR provides clinical workflow management for healthcare facilities:

- **Role-based access**: Administrator, Doctor, Nurse, Receptionist
- **Patient management**: Register, view, and edit patient records
- **Medical records**: Encounter notes, diagnoses, prescriptions
- **Appointment scheduling**: Create, view, and manage appointments
- **Audit logging**: Full tracking of all system actions
- **Security**: JWT-based auth, account lockout, MFA-ready

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 16 (App Router) |
| UI | React 19, Tailwind CSS 4, Radix UI |
| Language | TypeScript |
| ORM | Prisma 7 |
| Database | PostgreSQL (Neon serverless) |
| Auth | JWT (bcryptjs, jsonwebtoken) |
| Deployment | Vercel (serverless) |
| Validation | Zod |

## Getting Started

### Prerequisites

- Node.js 20+
- npm
- PostgreSQL (for local dev) or a Neon connection string

### Setup

```bash
# Install dependencies
npm install

# Generate Prisma client
npx prisma generate

# Configure environment
cp .env.example .env
```

Edit `.env` with your database credentials and JWT secrets.

### Seed the Database

```bash
npx prisma db seed
```

Default seed accounts:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Administrator |
| doctor1 | doctor123 | Doctor |
| doctor2 | doctor123 | Doctor |
| nurse1 | nurse123 | Nurse |
| reception1 | reception123 | Receptionist |

### Development

```bash
npm run dev
```

Open http://localhost:3000

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server (Turbopack) |
| `npm run build` | Production build |
| `npm start` | Run production server |
| `npm run lint` | Lint codebase |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (Neon) |
| `DIRECT_URL` | Yes | Direct DB connection for migrations |
| `JWT_SECRET_KEY` | Yes | Secret for signing JWT tokens |
| `JWT_ISSUER` | Yes | JWT issuer claim |
| `JWT_AUDIENCE` | Yes | JWT audience claim |
| `SECRET_KEY` | No | Fallback if JWT_SECRET_KEY unset |
| `JWT_ACCESS_TOKEN_MINUTES` | No | Token expiry (default: 30) |
| `ACCOUNT_LOCKOUT_ATTEMPTS` | No | Failed logins before lockout (default: 5) |
| `ACCOUNT_LOCKOUT_MINUTES` | No | Lockout duration (default: 15) |
| `AUTH_COOKIE_NAME` | No | Cookie name (default: ehr_access_token) |
| `EHR_ENCRYPTION_KEY` | No | Data encryption key |

## Deployment

Deployed on Vercel: **https://e-hr.vercel.app**

```bash
# Production build
npm run build

# Or deploy via Vercel CLI
vercel --prod
```

Set all required environment variables in the Vercel project dashboard before deploying.