import { z } from "zod";

const CATEGORIES = ["Medication", "Consumable", "Equipment", "Vaccine", "IV Fluid", "Lab Reagent", "Other"] as const;

export const supplySchema = z.object({
  name: z.string().min(1, "Name is required.").max(200),
  category: z.enum(CATEGORIES),
  quantity: z.coerce.number().int().min(0, "Quantity must be 0 or more."),
  unit: z.string().min(1, "Unit is required.").max(50),
  reorderLevel: z.coerce.number().int().min(0).default(10),
  unitCost: z.coerce.number().min(0).optional().nullable(),
  expiryDate: z.string().optional().or(z.literal("")),
  batchNumber: z.string().max(100).optional().or(z.literal("")),
  manufacturer: z.string().max(200).optional().or(z.literal("")),
  notes: z.string().max(1000).optional().or(z.literal("")),
});

export type SupplyInput = z.infer<typeof supplySchema>;
