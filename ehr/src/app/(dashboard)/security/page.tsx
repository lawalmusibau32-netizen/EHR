import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { StatsCard } from "@/components/shared/stats-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { formatTimestamp } from "@/lib/utils";

export default async function SecurityMonitoringPage() {
  const user = await getCurrentUser();
  if (!user || user.roleKey !== "administrator") redirect("/dashboard");

  const [failedLoginCount, securityEvents, lockedAccounts, actionSummary] = await Promise.all([
    prisma.auditLog.count({ where: { actionType: "LOGIN_FAILED" } }),
    prisma.auditLog.findMany({
      where: { actionType: { in: ["LOGIN_FAILED", "LOCKOUT", "MFA_FAILED", "UNAUTHORIZED", "LOGIN"] } },
      include: { user: { select: { displayName: true } } },
      orderBy: { createdAt: "desc" },
      take: 50,
    }),
    prisma.user.findMany({
      where: { lockedUntil: { gt: new Date() } },
      include: { role: true },
      orderBy: { lockedUntil: "desc" },
    }),
    prisma.auditLog.groupBy({
      by: ["actionType"],
      _count: true,
      orderBy: { _count: { actionType: "desc" } },
    }),
  ]);

  return (
    <div>
      <PageHeader title="Security Monitoring" description="Security events and account monitoring" />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatsCard label="Failed Logins" value={failedLoginCount} tone="warning" />
        <StatsCard label="Security Events" value={securityEvents.length} tone="info" />
        <StatsCard label="Locked Accounts" value={lockedAccounts.length} tone="destructive" />
        <StatsCard label="Active Users" value={await prisma.user.count({ where: { isActive: "Y" } })} tone="success" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Action Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {actionSummary.map((a) => (
                <div key={a.actionType} className="flex items-center justify-between text-sm">
                  <span>{a.actionType}</span>
                  <Badge variant="outline">{a._count}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {lockedAccounts.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Locked Accounts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {lockedAccounts.map((u) => (
                  <div key={u.userId} className="flex items-center justify-between text-sm">
                    <span>{u.displayName} ({u.username})</span>
                    <span className="text-xs text-destructive">
                      Locked until {u.lockedUntil?.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Security Events</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {securityEvents.map((event) => (
                <TableRow key={event.auditLogId}>
                  <TableCell className="text-xs">{formatTimestamp(event.createdAt)}</TableCell>
                  <TableCell className="text-xs">{event.user?.displayName ?? "System"}</TableCell>
                  <TableCell>
                    <Badge variant={
                      event.actionType === "LOGIN" ? "success" :
                      event.actionType === "LOGIN_FAILED" ? "destructive" :
                      event.actionType === "LOCKOUT" ? "destructive" :
                      event.actionType === "UNAUTHORIZED" ? "warning" : "default"
                    } className="text-[10px]">
                      {event.actionType}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">{event.details ?? "-"}</TableCell>
                </TableRow>
              ))}
              {securityEvents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">No security events.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
