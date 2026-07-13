import { z } from "zod";

export const patientSchema = z.object({
  mrn: z.string().min(1, "MRN is required.").max(30),
  firstName: z.string().min(1, "First name is required.").max(80),
  lastName: z.string().min(1, "Last name is required.").max(80),
  dateOfBirth: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Date of birth must be YYYY-MM-DD."),
  sex: z.enum(["Male", "Female", "Other"]),
  phoneNumber: z.string().max(30).optional().or(z.literal("")),
  email: z.string().email("Invalid email.").max(255).optional().or(z.literal("")),
  addressLine1: z.string().max(255).optional().or(z.literal("")),
  addressLine2: z.string().max(255).optional().or(z.literal("")),
  city: z.string().max(80).optional().or(z.literal("")),
  region: z.string().max(80).optional().or(z.literal("")),
  country: z.string().max(80).optional().or(z.literal("")),
  isActive: z.string().optional(),
});

export type PatientInput = z.infer<typeof patientSchema>;
