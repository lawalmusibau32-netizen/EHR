import { redirect } from "next/navigation";
import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/utils";
import { CancelAppointmentButton } from "@/components/appointments/cancel-button";

const statusVariant: Record<string, "default" | "success" | "warning" | "destructive" | "info" | "secondary"> = {
  SCHEDULED: "info",
  CHECKED_IN: "warning",
  COMPLETED: "success",
  CANCELLED: "destructive",
  NO_SHOW: "secondary",
};

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function AppointmentDetailPage({ params }: PageProps) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const { id } = await params;
  const appointment = await prisma.appointment.findUnique({
    where: { appointmentId: Number(id) },
    include: {
      patient: true,
      clinician: { select: { userId: true, displayName: true } },
      scheduler: { select: { userId: true, displayName: true } },
    },
  });

  if (!appointment) {
    return <div>Appointment not found.</div>;
  }

  return (
    <div>
      <PageHeader
        title="Appointment Details"
        description={`${appointment.appointmentType} • ${formatDateTime(appointment.appointmentDate)}`}
        actions={
          <div className="flex gap-2">
            {appointment.status !== "CANCELLED" && (
              <>
                <Button variant="outline" asChild>
                  <Link href={`/appointments/${appointment.appointmentId}/reschedule`}>Reschedule</Link>
                </Button>
                <CancelAppointmentButton appointmentId={appointment.appointmentId} />
              </>
            )}
            <Button variant="outline" asChild>
              <Link href="/appointments">Back</Link>
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Appointment Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-muted-foreground">Date & Time</span>
              <span>{formatDateTime(appointment.appointmentDate)}</span>
              <span className="text-muted-foreground">Type</span>
              <span>{appointment.appointmentType}</span>
              <span className="text-muted-foreground">Status</span>
              <span><Badge variant={statusVariant[appointment.status] ?? "default"}>{appointment.status}</Badge></span>
              <span className="text-muted-foreground">Location</span>
              <span>{appointment.location ?? "-"}</span>
              <span className="text-muted-foreground">Reason</span>
              <span>{appointment.reason ?? "-"}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Patient</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-muted-foreground">Name</span>
              <span>
                <Link href={`/patients/${appointment.patient.patientId}`} className="hover:underline font-medium">
                  {appointment.patient.firstName} {appointment.patient.lastName}
                </Link>
              </span>
              <span className="text-muted-foreground">MRN</span>
              <span className="font-mono">{appointment.patient.mrn}</span>
              <span className="text-muted-foreground">Clinician</span>
              <span>{appointment.clinician?.displayName ?? "-"}</span>
              <span className="text-muted-foreground">Scheduled By</span>
              <span>{appointment.scheduler.displayName}</span>
            </div>
          </CardContent>
        </Card>

        {appointment.notes && (
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm whitespace-pre-wrap">{appointment.notes}</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
