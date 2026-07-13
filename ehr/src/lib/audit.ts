import { prisma } from "./prisma";

export function audit(
  userId: number | null,
  actionType: string,
  entityName: string,
  entityId: string,
  details?: string | null,
  ipAddress?: string | null
): void {
  prisma.auditLog
    .create({
      data: {
        userId,
        actionType,
        entityName,
        entityId,
        details,
        ipAddress,
      },
    })
    .catch(() => {
      // Audit failures should never break the main flow
    });
}
