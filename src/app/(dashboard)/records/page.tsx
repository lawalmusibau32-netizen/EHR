import { redirect } from "next/navigation";
import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { SearchInput } from "@/components/shared/search-input";
import { RecordsTable } from "@/components/records/records-table";
import { Button } from "@/components/ui/button";

interface PageProps {
  searchParams: Promise<{ q?: string; record_type?: string }>;
}

export default async function RecordsPage({ searchParams }: PageProps) {
  const user = await getCurrentUser();
  if (!user || !["administrator", "doctor", "nurse"].includes(user.roleKey)) {
    redirect("/dashboard");
  }

  const params = await searchParams;
  const search = params.q?.trim() ?? "";
  const recordType = params.record_type || undefined;

  const where: Record<string, unknown> = {};
  if (recordType) where.recordType = recordType;
  if (search) {
    where.OR = [
      { title: { contains: search } },
      { patientRecord: { mrn: { contains: search } } },
      { patientRecord: { firstName: { contains: search } } },
      { patientRecord: { lastName: { contains: search } } },
    ];
  }

  const raw = await prisma.medicalRecord.findMany({
    where,
    include: {
      patient: { select: { displayName: true } },
      patientRecord: { select: { patientId: true, mrn: true, firstName: true, lastName: true } },
      _count: {
        select: {
          diagnoses: { where: { isActive: "Y" } },
          prescriptions: { where: { isActive: "Y" } },
          treatments: { where: { isActive: "Y" } },
        },
      },
    },
    orderBy: { encounterDate: "desc" },
  });

  const records = raw.map((r) => ({
    recordId: r.recordId,
    title: r.title,
    recordType: r.recordType,
    recordStatus: r.recordStatus,
    encounterDate: r.encounterDate,
    patient: r.patientRecord,
    createdByName: r.patient.displayName,
    diagnosisCount: r._count.diagnoses,
    prescriptionCount: r._count.prescriptions,
    treatmentCount: r._count.treatments,
  }));

  return (
    <div>
      <PageHeader
        title="Medical Records"
        description="Patient clinical records and documentation"
        actions={
          <Button asChild>
            <Link href="/records/new">New Record</Link>
          </Button>
        }
      />

      <div className="flex items-center gap-3 mb-4">
        <SearchInput placeholder="Search records..." />
      </div>

      <RecordsTable records={records} />
    </div>
  );
}
