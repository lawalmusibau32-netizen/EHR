import { redirect } from "next/navigation";
import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { SearchInput } from "@/components/shared/search-input";
import { AppointmentsTable } from "@/components/appointments/appointments-table";
import { Button } from "@/components/ui/button";

interface PageProps {
  searchParams: Promise<{ q?: string; status?: string }>;
}

export default async function AppointmentsPage({ searchParams }: PageProps) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const params = await searchParams;
  const search = params.q?.trim() ?? "";
  const status = params.status || undefined;

  const where: Record<string, unknown> = {};
  if (status) where.status = status;
  if (search) {
    where.OR = [
      { patient: { mrn: { contains: search } } },
      { patient: { firstName: { contains: search } } },
      { patient: { lastName: { contains: search } } },
    ];
  }

  const appointments = await prisma.appointment.findMany({
    where,
    include: {
      patient: { select: { patientId: true, mrn: true, firstName: true, lastName: true } },
      clinician: { select: { userId: true, displayName: true } },
      scheduler: { select: { userId: true, displayName: true } },
    },
    orderBy: { appointmentDate: "desc" },
  });

  return (
    <div>
      <PageHeader
        title="Appointments"
        description="Schedule and manage appointments"
        actions={
          <Button asChild>
            <Link href="/appointments/new">New Appointment</Link>
          </Button>
        }
      />

      <div className="flex items-center gap-3 mb-4">
        <SearchInput placeholder="Search appointments..." />
      </div>

      <AppointmentsTable appointments={appointments} />
    </div>
  );
}
