export const ROLE_ALIASES: Record<string, string> = {
  administrator: "administrator",
  admin: "administrator",
  doctor: "doctor",
  clinician: "doctor",
  nurse: "nurse",
  receptionist: "receptionist",
};

export const ROLE_LABELS: Record<string, string> = {
  administrator: "Administrator",
  doctor: "Doctor",
  nurse: "Nurse",
  receptionist: "Receptionist",
};

export function normalizeRoleKey(roleName: string | null): string {
  if (!roleName) return "";
  return ROLE_ALIASES[roleName.trim().toLowerCase()] ?? roleName.trim().toLowerCase();
}

export function roleLabel(roleKey: string): string {
  return ROLE_LABELS[normalizeRoleKey(roleKey)] ?? roleKey.charAt(0).toUpperCase() + roleKey.slice(1);
}

export type RoleKey = "administrator" | "doctor" | "nurse" | "receptionist";
