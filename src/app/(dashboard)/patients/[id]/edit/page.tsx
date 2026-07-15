import { redirect, notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { PatientForm } from "@/components/patients/patient-form";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function EditPatientPage({ params }: PageProps) {
  const user = await getCurrentUser();
  if (!user || !["administrator", "doctor", "receptionist"].includes(user.roleKey)) {
    redirect("/patients");
  }

  const { id } = await params;
  const patient = await prisma.patient.findUnique({
    where: { patientId: Number(id) },
  });

  if (!patient) {
    notFound();
  }

  return (
    <div>
      <PageHeader
        title="Edit Patient"
        description={`${patient.firstName} ${patient.lastName} (${patient.mrn})`}
      />
      <PatientForm patient={patient} action="Edit" />
    </div>
  );
}
