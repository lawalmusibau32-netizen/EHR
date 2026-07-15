import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { AppointmentForm } from "@/components/appointments/appointment-form";

interface PageProps {
  searchParams: Promise<{ patientId?: string }>;
}

export default async function NewAppointmentPage({ searchParams }: PageProps) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const params = await searchParams;
  const defaultPatientId = params.patientId ? Number(params.patientId) : undefined;

  const [patients, clinicians] = await Promise.all([
    prisma.patient.findMany({
      where: { isActive: "Y" },
      orderBy: [{ lastName: "asc" }, { firstName: "asc" }],
    }),
    prisma.user.findMany({
      where: {
        isActive: "Y",
        role: { roleName: { in: ["Doctor", "Administrator"] } },
      },
      include: { role: true },
      orderBy: { displayName: "asc" },
    }),
  ]);

  return (
    <div>
      <PageHeader title="Schedule Appointment" description="Book a new patient appointment" />
      <AppointmentForm
        patients={patients}
        clinicians={clinicians}
        defaultPatientId={defaultPatientId}
      />
    </div>
  );
}
