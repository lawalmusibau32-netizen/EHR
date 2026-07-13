import { z } from "zod";

const RECORD_TYPES = ["Encounter", "Diagnosis", "Medication", "Lab Result", "Imaging", "Procedure", "Note"] as const;
const RECORD_STATUSES = ["ACTIVE", "AMENDED", "VOID"] as const;
const DIAGNOSIS_STATUSES = ["ACTIVE", "RESOLVED", "RULE_OUT"] as const;

export const recordSchema = z.object({
  patientId: z.coerce.number().min(1, "Patient is required."),
  recordType: z.enum(RECORD_TYPES),
  title: z.string().min(1, "Title is required.").max(150),
  clinicalNote: z.string().min(1, "Clinical note is required.").max(10000),
  recordStatus: z.enum(RECORD_STATUSES).optional(),
  encounterDate: z.string().optional(),
});

export const diagnosisSchema = z.object({
  diagnosisName: z.string().min(1, "Diagnosis name is required.").max(255),
  icd10Code: z.string().max(12).optional().or(z.literal("")),
  diagnosisStatus: z.enum(DIAGNOSIS_STATUSES).optional(),
  isPrimary: z.string().optional(),
  diagnosedAt: z.string().optional(),
});

export const prescriptionSchema = z.object({
  medicationName: z.string().min(1, "Medication name is required.").max(255),
  dosage: z.string().max(255).optional().or(z.literal("")),
  frequency: z.string().max(255).optional().or(z.literal("")),
  route: z.string().max(255).optional().or(z.literal("")),
  durationDays: z.coerce.number().int().positive().optional().nullable(),
  instructions: z.string().optional().or(z.literal("")),
  prescribedAt: z.string().optional(),
});

export const treatmentSchema = z.object({
  treatmentName: z.string().min(1, "Treatment name is required.").max(255),
  treatmentDescription: z.string().optional().or(z.literal("")),
  treatmentDate: z.string().optional(),
  outcome: z.string().optional().or(z.literal("")),
  notes: z.string().optional().or(z.literal("")),
});

export type RecordInput = z.infer<typeof recordSchema>;
export type DiagnosisInput = z.infer<typeof diagnosisSchema>;
export type PrescriptionInput = z.infer<typeof prescriptionSchema>;
export type TreatmentInput = z.infer<typeof treatmentSchema>;
