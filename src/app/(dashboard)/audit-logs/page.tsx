import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { formatTimestamp } from "@/lib/utils";
import { SearchInput } from "@/components/shared/search-input";

interface PageProps {
  searchParams: Promise<{ q?: string; action_type?: string }>;
}

export default async function AuditLogsPage({ searchParams }: PageProps) {
  const user = await getCurrentUser();
  if (!user || user.roleKey !== "administrator") redirect("/dashboard");

  const params = await searchParams;
  const search = params.q?.trim() ?? "";
  const actionType = params.action_type || undefined;

  const where: Record<string, unknown> = {};
  if (actionType) where.actionType = actionType;
  if (search) {
    where.OR = [
      { actionType: { contains: search } },
      { entityName: { contains: search } },
      { entityId: { contains: search } },
      { details: { contains: search } },
      { user: { displayName: { contains: search } } },
      { user: { username: { contains: search } } },
    ];
  }

  const [logs, actionSummary] = await Promise.all([
    prisma.auditLog.findMany({
      where,
      include: { user: { select: { displayName: true, username: true } } },
      orderBy: { createdAt: "desc" },
      take: 100,
    }),
    prisma.auditLog.groupBy({
      by: ["actionType"],
      _count: true,
      orderBy: { _count: { actionType: "desc" } },
    }),
  ]);

  return (
    <div>
      <PageHeader title="Audit Logs" description="System activity and change tracking" />

      <div className="flex items-center gap-3 mb-4">
        <SearchInput placeholder="Search audit logs..." />
      </div>

      {actionSummary.length > 0 && (
        <div className="flex gap-2 mb-4 flex-wrap">
          {actionSummary.map((a) => (
            <Badge key={a.actionType} variant="outline" className="text-xs">
              {a.actionType}: {a._count}
            </Badge>
          ))}
        </div>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>User</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Entity</TableHead>
              <TableHead>Details</TableHead>
              <TableHead>IP Address</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.auditLogId}>
                <TableCell className="text-xs whitespace-nowrap">{formatTimestamp(log.createdAt)}</TableCell>
                <TableCell className="text-xs">{log.user?.displayName ?? "System"}</TableCell>
                <TableCell>
                  <Badge variant={
                    log.actionType === "LOGIN" ? "success" :
                    log.actionType === "LOGIN_FAILED" ? "destructive" :
                    log.actionType === "LOGOUT" ? "secondary" :
                    log.actionType === "CREATE" ? "info" :
                    log.actionType === "DELETE" ? "warning" : "default"
                  } className="text-[10px]">
                    {log.actionType}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs">
                  {log.entityName}
                  <span className="text-muted-foreground ml-1">#{log.entityId}</span>
                </TableCell>
                <TableCell className="text-xs max-w-[200px] truncate">{log.details ?? "-"}</TableCell>
                <TableCell className="text-xs font-mono">{log.ipAddress ?? "-"}</TableCell>
              </TableRow>
            ))}
            {logs.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground py-8">No audit logs found.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
