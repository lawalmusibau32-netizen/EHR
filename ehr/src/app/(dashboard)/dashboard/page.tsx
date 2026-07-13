import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { StatsCard } from "@/components/shared/stats-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatTimestamp } from "@/lib/utils";
import Link from "next/link";
import { Activity, ArrowRight, Pill } from "lucide-react";

async function LowStockSupplies() {
  const lowSupplies = await prisma.inventorySupply.findMany({
    where: { isActive: "Y", quantity: { lte: prisma.inventorySupply.fields.reorderLevel } },
    orderBy: { quantity: "asc" },
    take: 5,
  });

  if (lowSupplies.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Pill className="h-4 w-4 text-amber-500" />
            <CardTitle>Low Stock Alerts</CardTitle>
          </div>
          <Link
            href="/supplies"
            className="flex items-center gap-1 text-xs text-primary/60 hover:text-primary transition-colors"
          >
            View inventory <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {lowSupplies.map((s, i) => (
            <div key={s.supplyId} className="flex items-center justify-between text-sm py-2 px-3 rounded-lg bg-amber-500/5 border border-amber-500/10" style={{ animationDelay: `${i * 0.05}s` }}>
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-medium text-amber-600 dark:text-amber-400">{s.name}</span>
                <Badge variant="outline" className="text-[10px]">{s.category}</Badge>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs text-muted-foreground">{s.quantity} / {s.reorderLevel} {s.unit}</span>
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/supplies/${s.supplyId}/edit`}>Restock</Link>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default async function DashboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const roleKey = user.roleKey;

  const getStats = async () => {
    const base = {
      patients: await prisma.patient.count({ where: { isActive: "Y" } }),
      appointments: await prisma.appointment.count(),
    };

    switch (roleKey) {
      case "administrator":
        return {
          cards: [
            { label: "Active Users", value: await prisma.user.count({ where: { isActive: "Y" } }), tone: "primary" as const },
            { label: "Patients", value: base.patients, tone: "success" as const },
            { label: "Audit Events", value: await prisma.auditLog.count(), tone: "info" as const },
            { label: "Failed Logins", value: await prisma.auditLog.count({ where: { actionType: "LOGIN_FAILED" } }), tone: "warning" as const },
          ],
        };
      case "doctor":
        return {
          cards: [
            { label: "Upcoming Appointments", value: await prisma.appointment.count({ where: { status: { in: ["SCHEDULED", "CHECKED_IN"] } } }), tone: "primary" as const },
            { label: "Medical Records", value: await prisma.medicalRecord.count(), tone: "success" as const },
            { label: "Active Patients", value: base.patients, tone: "info" as const },
            { label: "Active Records", value: await prisma.medicalRecord.count({ where: { recordStatus: "ACTIVE" } }), tone: "warning" as const },
          ],
        };
      case "nurse":
        return {
          cards: [
            { label: "Checked In", value: await prisma.appointment.count({ where: { status: "CHECKED_IN" } }), tone: "success" as const },
            { label: "Scheduled", value: await prisma.appointment.count({ where: { status: "SCHEDULED" } }), tone: "primary" as const },
            { label: "Active Patients", value: base.patients, tone: "info" as const },
            { label: "No Shows", value: await prisma.appointment.count({ where: { status: "NO_SHOW" } }), tone: "warning" as const },
          ],
        };
      default:
        return {
          cards: [
            { label: "Scheduled Visits", value: await prisma.appointment.count({ where: { status: "SCHEDULED" } }), tone: "primary" as const },
            { label: "Checked In", value: await prisma.appointment.count({ where: { status: "CHECKED_IN" } }), tone: "success" as const },
            { label: "Patients", value: base.patients, tone: "info" as const },
            { label: "Cancelled", value: await prisma.appointment.count({ where: { status: "CANCELLED" } }), tone: "warning" as const },
          ],
        };
    }
  };

  const stats = await getStats();

  const recentActivity = await prisma.auditLog.findMany({
    include: { user: { select: { displayName: true } } },
    orderBy: { createdAt: "desc" },
    take: 6,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground/90">
            Welcome back,{" "}
            <span className="text-gradient">{user.username}</span>
          </h1>
          <p className="text-sm text-muted-foreground/60 mt-1">Here&apos;s what&apos;s happening with your system today.</p>
        </div>
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/5 border border-primary/10 text-xs text-primary/70">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
          </span>
          System Online
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.cards.map((card, i) => (
          <div key={i} className="animate-slide-up" style={{ animationDelay: `${i * 0.1}s` }}>
            <StatsCard {...card} />
          </div>
        ))}
      </div>

      <LowStockSupplies />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary/60" />
              <CardTitle>Recent Activity</CardTitle>
            </div>
            <Link
              href="/audit-logs"
              className="flex items-center gap-1 text-xs text-primary/60 hover:text-primary transition-colors"
            >
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {recentActivity.length === 0 && (
              <div className="text-sm text-muted-foreground/60 py-4 text-center">No recent activity recorded.</div>
            )}
            {recentActivity.map((log, i) => (
              <div
                key={log.auditLogId}
                className="flex items-center justify-between text-sm py-2 px-3 rounded-lg hover:bg-white/[0.03] transition-colors"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Badge variant={
                    log.actionType === "LOGIN" ? "success" :
                    log.actionType === "LOGIN_FAILED" ? "destructive" :
                    log.actionType === "CREATE" ? "info" :
                    log.actionType === "DELETE" ? "warning" : "default"
                  } className="text-[10px] shrink-0">
                    {log.actionType}
                  </Badge>
                  <span className="text-foreground/70 truncate">{log.user?.displayName ?? "System"}</span>
                  <span className="text-muted-foreground/50 hidden md:inline truncate">{log.details ?? `on ${log.entityName} #${log.entityId}`}</span>
                </div>
                <span className="text-xs text-muted-foreground/40 shrink-0 ml-2">{formatTimestamp(log.createdAt)}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
