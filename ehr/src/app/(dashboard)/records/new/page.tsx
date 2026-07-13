import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { RecordForm } from "@/components/records/record-form";

interface PageProps {
  searchParams: Promise<{ patientId?: string }>;
}

export default async function NewRecordPage({ searchParams }: PageProps) {
  const user = await getCurrentUser();
  if (!user || !["administrator", "doctor", "nurse"].includes(user.roleKey)) {
    redirect("/records");
  }

  const params = await searchParams;
  const defaultPatientId = params.patientId ? Number(params.patientId) : undefined;

  const patients = await prisma.patient.findMany({
    where: { isActive: "Y" },
    orderBy: [{ lastName: "asc" }, { firstName: "asc" }],
  });

  return (
    <div>
      <PageHeader title="New Medical Record" description="Create a clinical record entry" />
      <RecordForm patients={patients} defaultPatientId={defaultPatientId} />
    </div>
  );
}
