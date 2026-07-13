import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/utils";

const statusVariant: Record<string, "default" | "success" | "warning" | "destructive" | "info" | "secondary"> = {
  SCHEDULED: "info",
  CHECKED_IN: "warning",
  COMPLETED: "success",
  CANCELLED: "destructive",
  NO_SHOW: "secondary",
};

interface AppointmentRow {
  appointmentId: number;
  appointmentDate: Date;
  appointmentType: string;
  status: string;
  patient: { patientId: number; mrn: string; firstName: string; lastName: string };
  clinician?: { displayName: string } | null;
}

interface AppointmentsTableProps {
  appointments: AppointmentRow[];
}

export function AppointmentsTable({ appointments }: AppointmentsTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date & Time</TableHead>
            <TableHead>Patient</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Clinician</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {appointments.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                No appointments found.
              </TableCell>
            </TableRow>
          )}
          {appointments.map((apt) => (
            <TableRow key={apt.appointmentId}>
              <TableCell>{formatDateTime(apt.appointmentDate)}</TableCell>
              <TableCell>
                <Link href={`/patients/${apt.patient.patientId}`} className="font-medium hover:underline">
                  {apt.patient.lastName}, {apt.patient.firstName}
                </Link>
                <div className="text-xs text-muted-foreground font-mono">{apt.patient.mrn}</div>
              </TableCell>
              <TableCell>{apt.appointmentType}</TableCell>
              <TableCell>{apt.clinician?.displayName ?? "-"}</TableCell>
              <TableCell>
                <Badge variant={statusVariant[apt.status] ?? "default"}>{apt.status}</Badge>
              </TableCell>
              <TableCell className="text-right">
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/appointments/${apt.appointmentId}`}>View</Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
