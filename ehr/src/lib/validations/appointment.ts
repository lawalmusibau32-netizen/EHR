import { z } from "zod";

const APPOINTMENT_TYPES = ["Consultation", "Follow-up", "Procedure", "Telehealth", "Lab Review", "Referral"] as const;
const STATUSES = ["SCHEDULED", "CHECKED_IN", "COMPLETED", "CANCELLED", "NO_SHOW"] as const;

export const appointmentSchema = z.object({
  patientId: z.coerce.number().min(1, "Patient is required."),
  clinicianUserId: z.coerce.number().optional().nullable(),
  appointmentDate: z.string().min(1, "Date and time are required."),
  appointmentType: z.enum(APPOINTMENT_TYPES),
  status: z.enum(STATUSES).optional(),
  reason: z.string().max(255).optional().or(z.literal("")),
  location: z.string().max(120).optional().or(z.literal("")),
  notes: z.string().max(4000).optional().or(z.literal("")),
});

export type AppointmentInput = z.infer<typeof appointmentSchema>;
