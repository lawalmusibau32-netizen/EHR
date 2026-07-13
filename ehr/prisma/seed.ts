import { PrismaClient } from "../src/lib/prisma-client/client";
import { PrismaNeon } from "@prisma/adapter-neon";
import bcrypt from "bcryptjs";

async function main() {
  const adapter = new PrismaNeon({ connectionString: process.env.DATABASE_URL! });
  const prisma = new PrismaClient({ adapter });

  console.log("Seeding database...");

  const now = new Date();

  await Promise.all([
    prisma.role.upsert({ where: { roleId: 1 }, update: {}, create: { roleId: 1, roleName: "Administrator", description: "Full system access", isSystem: "Y", createdAt: now } }),
    prisma.role.upsert({ where: { roleId: 2 }, update: {}, create: { roleId: 2, roleName: "Doctor", description: "Clinical access", isSystem: "Y", createdAt: now } }),
    prisma.role.upsert({ where: { roleId: 3 }, update: {}, create: { roleId: 3, roleName: "Nurse", description: "Nursing access", isSystem: "Y", createdAt: now } }),
    prisma.role.upsert({ where: { roleId: 4 }, update: {}, create: { roleId: 4, roleName: "Receptionist", description: "Front desk access", isSystem: "Y", createdAt: now } }),
  ]);

  const hash = bcrypt.hashSync("admin123", 12);
  const hashDoctor = bcrypt.hashSync("doctor123", 12);
  const hashNurse = bcrypt.hashSync("nurse123", 12);
  const hashReception = bcrypt.hashSync("reception123", 12);

  await Promise.all([
    prisma.user.upsert({ where: { userId: 1 }, update: {}, create: { userId: 1, roleId: 1, username: "admin", displayName: "System Administrator", email: "admin@healthiq.com", passwordHash: hash, createdAt: now, updatedAt: now } }),
    prisma.user.upsert({ where: { userId: 2 }, update: {}, create: { userId: 2, roleId: 2, username: "doctor1", displayName: "Dr. Kwame Asante", email: "doctor1@healthiq.com", passwordHash: hashDoctor, createdAt: now, updatedAt: now } }),
    prisma.user.upsert({ where: { userId: 3 }, update: {}, create: { userId: 3, roleId: 2, username: "doctor2", displayName: "Dr. Esi Baidoo", email: "doctor2@healthiq.com", passwordHash: hashDoctor, createdAt: now, updatedAt: now } }),
    prisma.user.upsert({ where: { userId: 4 }, update: {}, create: { userId: 4, roleId: 3, username: "nurse1", displayName: "Nurse Adwoa Sarpong", email: "nurse1@healthiq.com", passwordHash: hashNurse, createdAt: now, updatedAt: now } }),
    prisma.user.upsert({ where: { userId: 5 }, update: {}, create: { userId: 5, roleId: 4, username: "reception1", displayName: "Yvonne Ofori", email: "reception1@healthiq.com", passwordHash: hashReception, createdAt: now, updatedAt: now } }),
  ]);

  const patientData = [
    { mrn: "MRN-001", fname: "Kofi", lname: "Mensah", dob: "1985-03-15", sex: "Male", phone: "+233 20 111 1111", email: "kofi.mensah@example.com", addr: "12 Independence Ave", city: "Accra", region: "Greater Accra" },
    { mrn: "MRN-002", fname: "Ama", lname: "Osei", dob: "1992-07-22", sex: "Female", phone: "+233 24 222 2222", email: "ama.osei@example.com", addr: "45 Ring Road", city: "Kumasi", region: "Ashanti" },
    { mrn: "MRN-003", fname: "Yaw", lname: "Adjei", dob: "1978-11-02", sex: "Male", phone: "+233 50 333 3333", email: "yaw.adjei@example.com", addr: "78 Ocean Road", city: "Takoradi", region: "Western" },
  ];

  for (const p of patientData) {
    const existing = await prisma.patient.findUnique({ where: { mrn: p.mrn } });
    if (!existing) {
      await prisma.patient.create({
        data: {
          mrn: p.mrn, firstName: p.fname, lastName: p.lname,
          dateOfBirth: new Date(p.dob), sex: p.sex,
          phoneNumber: p.phone, email: p.email,
          addressLine1: p.addr, city: p.city, region: p.region, country: "Ghana",
        },
      });
    }
  }

  const recordCount = await prisma.medicalRecord.count();
  if (recordCount === 0) {
    const pastDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    const futureDate = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000);
    const nearDate = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);

    await prisma.medicalRecord.create({
      data: {
        patientId: 1, createdByUserId: 1, recordType: "Encounter",
        title: "Initial Consultation",
        clinicalNote: "Patient presents with mild hypertension. BP 140/90. Advised lifestyle modifications. Follow-up in 4 weeks.",
        encounterDate: pastDate,
        diagnoses: { create: { diagnosisName: "Essential Hypertension", icd10Code: "I10", diagnosisStatus: "ACTIVE", isPrimary: "Y", diagnosedAt: pastDate } },
        prescriptions: { create: { medicationName: "Amlodipine", dosage: "5mg", frequency: "Once daily", route: "Oral", durationDays: 30, instructions: "Take in the morning.", prescribedAt: pastDate } },
      },
    });

    await prisma.appointment.create({ data: { patientId: 1, scheduledByUserId: 1, appointmentDate: futureDate, appointmentType: "Follow-up", status: "SCHEDULED", reason: "Hypertension follow-up", location: "Room 204" } });
    await prisma.appointment.create({ data: { patientId: 2, scheduledByUserId: 1, appointmentDate: nearDate, appointmentType: "Consultation", status: "SCHEDULED", reason: "Annual checkup", location: "Room 101" } });
    console.log("Medical records and appointments created.");
  }

  await prisma.auditLog.create({ data: { userId: 1, actionType: "LOGIN", entityName: "seed", entityId: "1", details: "Database seeded." } });
  console.log("Seeding complete.");
  await prisma.$disconnect();
}

main().catch((e) => { console.error(e); process.exit(1); });
